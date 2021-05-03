import sys
import yaml
import json
import logging
import requests as re
from dataclasses import dataclass, field

logging.basicConfig(level=logging.WARNING)

@dataclass()
class Adguard:
    """
    Instance of adguard
    """
    url: str
    username: str
    password: str
    verify_ssl: bool = field(default=True)


@dataclass
class Record:
    """
    DNS-Record with:
    name: test.de  (e.g.)
    address: 1.1.1.1 (e.g.)
    """
    name: str
    address: str


class AdguardSync:
    # All adguards
    adguards: list[Adguard] = []
    # Records from config file
    config_records: list[Record] = []

    def __init__(self, file_name):
        configuration = AdguardSync.read_yaml(file_name=file_name)
        self.parse_configuration(configuration=configuration)
        self.process()

    @staticmethod
    def read_yaml(file_name: str) -> dict:
        """
        Reads a file and tries to parse it as YAML file.

        :param file_name: Path to the file
        :return: Structure of YAML in python format
        """
        try:
            with open(file_name, 'r') as fh:
                yaml_file = yaml.safe_load(fh)
                if not yaml_file:
                    logging.error("Invalid YAML file!")
                    exit(1)

                return yaml_file
        except FileNotFoundError:
            print("File not found")

    def parse_configuration(self, configuration) -> None:
        """
        Parses the parsed YAML to object variables
        :param configuration:
        """

        for adguard in configuration["adguards"]:
            ad_class = Adguard(url=adguard['hostname'], username=adguard['username'],
                               password=adguard['password'])

            if "verify_ssl" in adguard:
                ad_class.verify_ssl = adguard["verify_ssl"]

            self.adguards.append(ad_class)

        for record in configuration["dns_records"]:
            self.config_records.append(Record(name=record['domain'], address=record['address']))

    def check_dns_records(self, adguard) -> list[list[Record], list[Record]]:
        """
        Checks whether a record has to be deleted, edited or created

        :return: two lists of records to be deleted and created
        """
        to_be_deleted: list[Record] = []
        to_be_created: list[Record] = []

        req = re.get(f"{adguard.url}/control/rewrite/list",
                     auth=(adguard.username, adguard.password), verify=adguard.verify_ssl)

        if req.status_code != 200:
            logging.error(f"Could not connect to {adguard.url}. Code: {req.status_code}")
            return [[], []]

        adguard_records: dict[str: str, str: str] = req.json()

        # Check which records are on adguard only. They should get deleted also
        for adguard_record in adguard_records:
            record = Record(name=adguard_record["domain"], address=adguard_record["answer"])
            if record not in self.config_records:
                logging.debug(f"Record {record.name} not found. Will be deleted...")
                to_be_deleted.append(record)


        for config_record in self.config_records:
            logging.debug(f"--- Checking {config_record.name}")
            found = False
            changed = False

            for adguard_record in adguard_records:
                if adguard_record["domain"] == config_record.name:
                    found = True
                    if adguard_record["answer"] != config_record.address:
                        logging.debug(f"Need to change {adguard_record['answer']} to "
                                      f"{config_record.address}")
                        changed = True
                        to_be_deleted.append(Record(name=config_record.name, address=adguard_record['answer']))
                        to_be_created.append(config_record)

                    break

            if found and not changed:
                logging.debug("Correct record already exists")
            elif not found:
                logging.debug("Record is missing. Will be created.")
                to_be_created.append(config_record)

        return [to_be_created, to_be_deleted]

    @staticmethod
    def act_on_records(adguard: Adguard, records: list[Record], create=True) -> None:
        """
        Creates or deletes records.

        :param adguard: The adguard to act on
        :param records: The records that should be created/deleted
        :param create: Boolean whether the record should be created or deleted
        """
        for record in records:
            record: Record = record

            data = {
                "domain": record.name,
                "answer": record.address
            }

            url = f"{adguard.url}/control/rewrite/add"
            if not create:
                url = f"{adguard.url}/control/rewrite/delete"

            req = re.post(url, data=json.dumps(data), auth=(adguard.username, adguard.password),
                          verify=adguard.verify_ssl)

            if req.status_code != 200:
                action = "create"
                if not create:
                    action = "delete"

                logging.warning(f"Unable to {action} DNS record {record.name}: {req.text}")

    def delete_records(self, adguard: Adguard, to_be_deleted: list[Record]) -> None:
        """
        Delete records on adguard.

        :param adguard: The adguard to act on
        :param to_be_deleted: The list of records that should be deleted
        """
        self.act_on_records(adguard=adguard, records=to_be_deleted, create=False)

    def create_records(self, adguard: Adguard, to_be_created: list[Record]) -> None:
        """
        Create records on adguard.

        :param adguard: The adguard to act on
        :param to_be_created: The list of records that should be created
        """
        self.act_on_records(adguard=adguard, records=to_be_created)

    def process(self) -> None:
        """
        Check DNS records on all adguards. Then create and/or delete them
        if needed.
        """
        for adguard in self.adguards:
            adguard: Adguard = adguard

            logging.debug(f"{'-' * 15} {adguard.url}")
            create, delete = self.check_dns_records(adguard)

            self.delete_records(adguard, delete)
            self.create_records(adguard, create)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        logging.error("Specify a config file to start")
        exit(1)

    filename = sys.argv[1]
    AdguardSync(file_name=sys.argv[1])
