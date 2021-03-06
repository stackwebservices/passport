from unittest import TestCase

from nose.tools import eq_
from mock import patch, mock_open

from passport import create_app
from passport.api.exceptions import (ApiException, RequestDataException)
from passport.api.common.failures import Failures as CommonFailures
from passport.api.roles.schema import RoleSchema
from passport.models import Role

from ...mocks.common import role_data


class SchemaTests(TestCase):

    def setUp(self):
        self.app = create_app(settings_override={
            'SQLALCHEMY_DATABASE_URI': "sqlite://"
        })
        self.app.config['TESTING'] = True

    @patch('passport.api.roles.schema.Role')
    def test_role_load_without_id(self, mock_role):
        schema = RoleSchema()
        role_json = role_data(json=False)
        role = Role(**role_json)
        mock_role.return_value = role
        mock_role.query.filter.return_value.first.return_value = None
        with self.app.app_context():
            response_object, errors = schema.load(role_json, partial=('id',))
        eq_(errors, {})
        eq_(response_object, role)

    
    @patch('passport.api.roles.schema.Role')
    def test_role_load_name_registered(self, mock_role):
        schema = RoleSchema()
        role_json = role_data(json=False)
        mock_role.query.filter.return_value.first.return_value = Role(name=role_json['name'])
        with self.app.app_context(), self.assertRaises(RequestDataException) as error_context:
            response_object, errors = schema.load(role_json, partial=('id',))
        failure = CommonFailures.name_already_exists
        failure['message'] = "role name already registered" 
        failure['details'] = "the name of your choice is already in usage"

        eq_(error_context.exception.errors, failure)


    @patch('passport.api.roles.schema.Role')
    def test_role_load_updating(self, mock_role):
        schema = RoleSchema()
        role_json = role_data(json=False)
        role_json['id'] = 1
        mock_role.query.filter.return_value.first.return_value = Role(id=1, name=role_json['name'])
        with self.app.app_context():
            schema.validate_name(role_json)


    @patch('passport.api.roles.schema.Role')
    def test_role_load_missing_fields(self, mock_role):
        schema = RoleSchema()
        role_json = role_data(json=False)
        role_json['id'] = None
        required_fields = self.get_schema_required_fields(RoleSchema)
        [role_json.pop(k) for k in required_fields]

        mock_role.query.filter.return_value.first.return_value = None

        with self.assertRaises(RequestDataException) as error_context:
            response_object, error = schema.load(role_json)

        eq_(
            set(error_context.exception.errors['details'].keys()) -
            set(required_fields),
            set([]))
        error_context.exception.errors['details'] = None
        eq_(error_context.exception.errors, CommonFailures.information_missing)

    def get_schema_required_fields(self, schema):
        return [k for k, v in schema._declared_fields.iteritems()
                if v.required and not v.dump_only]
    