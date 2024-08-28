#!/usr/bin/python3

from sqlalchemy.schema import CreateIndex, CreateTable

from matcher import database, model

DB_URL = "postgresql:///matcher"
database.init_db(DB_URL)


def create_db():
    model.Base.metadata.create_all(database.session.get_bind())


def print_create_table(classes):
    database.init_db(DB_URL)

    engine = database.session.get_bind()

    for cls in classes:
        sql = str(CreateTable(cls.__table__).compile(engine))
        print(sql.strip() + ";")

        for index in cls.__table__.indexes:
            sql = str(CreateIndex(index).compile(engine))
            print(sql.strip() + ";")


# print_create_table([model.ItemIsA])
# print_create_table([model.EditSession])
# print_create_table([model.Changeset, model.ChangesetEdit, model.SkipIsA])
# print_create_table([model.User])
# print_create_table([model.Extract])

create_db()
