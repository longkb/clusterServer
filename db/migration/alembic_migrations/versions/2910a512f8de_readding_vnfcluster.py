# Copyright 2017 OpenStack Foundation
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

"""Readding vnfcluster

Revision ID: 2910a512f8de
Revises: 8f2ecefd531c
Create Date: 2017-10-11 14:32:42.455281

"""

# revision identifiers, used by Alembic.
revision = '2910a512f8de'
down_revision = '8f2ecefd531c'

from alembic import op
import sqlalchemy as sa
from tacker.db.types import Json


from tacker.db import migration


def upgrade(active_plugins=None, options=None):
    print 'skip'