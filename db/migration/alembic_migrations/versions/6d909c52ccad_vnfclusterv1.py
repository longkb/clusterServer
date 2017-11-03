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

"""vnfclusterv1

Revision ID: 6d909c52ccad
Revises: 2ab513071424
Create Date: 2017-10-24 01:04:18.988815

"""

# revision identifiers, used by Alembic.
revision = '6d909c52ccad'
down_revision = '2ab513071424'

from alembic import op
import sqlalchemy as sa
from tacker.db import migration
from tacker.db.types import Json


def upgrade(active_plugins=None, options=None):
    print 'skip'