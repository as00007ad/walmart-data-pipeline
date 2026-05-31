import csv
import sqlite3


class DatabaseConnector:
    """
    Populates the Walmart shipment SQLite database from CSV files.
    """

    def __init__(self, database_file):
        self.connection = sqlite3.connect(database_file)
        self.cursor = self.connection.cursor()

    def populate(self, spreadsheet_folder):
        """
        Reads all three CSV spreadsheets and inserts their data
        into the product and shipment tables.
        """
        with open(f"{spreadsheet_folder}/shipping_data_0.csv", "r", newline="") as file_0, \
             open(f"{spreadsheet_folder}/shipping_data_1.csv", "r", newline="") as file_1, \
             open(f"{spreadsheet_folder}/shipping_data_2.csv", "r", newline="") as file_2:

            reader_0 = csv.reader(file_0)
            reader_1 = csv.reader(file_1)
            reader_2 = csv.reader(file_2)

            self.populate_from_shipping_data_0(reader_0)
            self.populate_from_shipping_data_1_and_2(reader_1, reader_2)

        self.connection.commit()

    def populate_from_shipping_data_0(self, reader_0):
        """
        Spreadsheet 0 is self-contained:
        origin, destination, product name, and quantity are present
        in the same row.
        """
        for row_index, row in enumerate(reader_0):
            if row_index == 0:
                continue

            origin = row[0]
            destination = row[1]
            product_name = row[2]
            quantity = int(row[4])

            self.insert_product_if_missing(product_name)
            self.insert_shipment(product_name, quantity, origin, destination)

    def populate_from_shipping_data_1_and_2(self, reader_1, reader_2):
        """
        Spreadsheet 1 has one product per row with a shipment identifier.
        Spreadsheet 2 has the origin and destination for each shipment.
        Rows are grouped by shipment identifier and product name to calculate
        product quantities.
        """
        shipments = {}

        for row_index, row in enumerate(reader_2):
            if row_index == 0:
                continue

            shipment_identifier = row[0]
            origin = row[1]
            destination = row[2]

            shipments[shipment_identifier] = {
                "origin": origin,
                "destination": destination,
                "products": {}
            }

        for row_index, row in enumerate(reader_1):
            if row_index == 0:
                continue

            shipment_identifier = row[0]
            product_name = row[1]

            products = shipments[shipment_identifier]["products"]
            products[product_name] = products.get(product_name, 0) + 1

        for shipment in shipments.values():
            origin = shipment["origin"]
            destination = shipment["destination"]

            for product_name, quantity in shipment["products"].items():
                self.insert_product_if_missing(product_name)
                self.insert_shipment(product_name, quantity, origin, destination)

    def insert_product_if_missing(self, product_name):
        """
        Inserts product name into product table if it is not already present.
        """
        query = """
        INSERT OR IGNORE INTO product (name)
        VALUES (?);
        """
        self.cursor.execute(query, (product_name,))

    def insert_shipment(self, product_name, quantity, origin, destination):
        """
        Finds product id and inserts shipment row.
        """
        product_id_query = """
        SELECT id
        FROM product
        WHERE name = ?;
        """
        self.cursor.execute(product_id_query, (product_name,))
        product_id = self.cursor.fetchone()[0]

        shipment_query = """
        INSERT INTO shipment (product_id, quantity, origin, destination)
        VALUES (?, ?, ?, ?);
        """
        self.cursor.execute(
            shipment_query,
            (product_id, quantity, origin, destination)
        )

    def close(self):
        self.connection.close()


if __name__ == "__main__":
    database = DatabaseConnector("shipment_database.db")
    database.populate("./data")
    database.close()
    print("Database populated successfully.")
