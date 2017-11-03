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

"""vnfcluster5

Revision ID: 76e024f79556
Revises: 85bb01f56a73
Create Date: 2017-10-27 03:17:54.023064

"""

# revision identifiers, used by Alembic.
revision = '76e024f79556'
down_revision = '85bb01f56a73'

from alembic import op
import sqlalchemy as sa
from tacker.db import migration
from tacker.db.types import Json


def upgrade(active_plugins=None, options=None):
    # op.drop_table('cluster_members')
    # op.drop_table('clusters')
    op.create_table(
        'vnfclusters',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=255), nullable=False),
        sa.Column('vnfd_id', sa.String(length=36), nullable=False),
        sa.Column('lb_id', sa.String(length=36), nullable=True),
        sa.Column('policy_info', Json, nullable=True),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB'
    )

    op.create_table(
        'vnfclustermembers',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('cluster_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.String(length=255), nullable=False),
        sa.Column('lb_member_id', sa.String(length=36), nullable=True),
        sa.Column('placement_attr', sa.String(length=255), nullable=False),
        sa.Column('cp_id', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['cluster_id'], ['vnfclusters.id'], ),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB'
    )
