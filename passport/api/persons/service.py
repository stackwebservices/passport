from jose import jws
from jose.constants import ALGORITHMS

from ...extensions import db
from ...models import Person

from ..utilities import get_rsa_private_key

from .schema import PersonSchema


schema = PersonSchema()


def person_schema_load(json):
    schema = PersonSchema()
    return schema.load(json or {})[0]


def person_schema_dump(person):
    return schema.dump(person)[0]


def save_and_dump_person(person):
    db.session.add(person)
    db.session.commit()

    return person_schema_dump(person)


def generate_jwt(user):
    person = Person.query.filter_by(user_id=user.id)
    schema = PersonSchema()

    response, response_errors = schema.dump(person)
    token = jws.sign(
        response, get_rsa_private_key(), algorithm=ALGORITHMS.RS256)

    return token