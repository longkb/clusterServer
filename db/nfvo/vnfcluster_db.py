# Copyright 2016 Red Hat Inc
# All Rights Reserved.
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

from oslo_utils import uuidutils
import random
import uuid
from oslo_log import log as logging
from six import iteritems
import time

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.orm import exc as orm_exc

from tacker.common import exceptions
from tacker.db import db_base
from tacker.db import model_base
from tacker.db import models_v1
from tacker.db import types
from tacker.extensions import nfvo
from tacker.extensions.nfvo_plugins import vnfcluster
from tacker.db.common_services import common_services_db_plugin
from tacker.common import exceptions
from tacker.plugins.common import constants

LOG = logging.getLogger(__name__)

class VnfCluster(model_base.BASE, models_v1.HasId, models_v1.HasTenant):
    """VNF Cluster Data Model"""
    __tablename__ = 'vnfclusters'
    __table_args__ = {'extend_existing': True}
    name = sa.Column(sa.String(255), nullable=True)
    description = sa.Column(sa.String(255), nullable=True)
    status = sa.Column(sa.String(255), nullable=False)
    vnfd_id = sa.Column(types.Uuid, nullable=False)
    lb_id=sa.Column(types.Uuid)
    cluster_members = orm.relationship("VnfClusterMember", backref="vnfcluster")
    policy_info = sa.Column(types.Json)

class VnfClusterMember(model_base.BASE, models_v1.HasId, models_v1.HasTenant):
    """VNF Cluster Member Data Model"""

    __tablename__ = 'vnfclustermembers'
    __table_args__ = {'extend_existing': True}
    name = sa.Column(sa.String(255), nullable=True)
    cluster_id = sa.Column(sa.String(255), sa.ForeignKey('vnfclusters.id'))
    role = sa.Column(sa.String(255), nullable=False)
    placement_attr = sa.Column(sa.String(255), nullable=True)
    lb_member_id = sa.Column(types.Uuid)
    cp_id = sa.Column(sa.String(255), nullable=True)

class VnfClusterPluginDb(vnfcluster.VnfClusterPluginBase, db_base.CommonDbMixin):

    def __init__(self):
        super(vnfcluster.VnfClusterPluginBase, self).__init__()
        self._cos_db_plg = common_services_db_plugin.CommonServicesPluginDb()

    def _get_resource(self, context, model, id):
        try:
            return self._get_by_id(context, model, id)
        except orm_exc.NoResultFound:
            if issubclass(model, VnfCluster):
                raise vnfcluster.VnfClusterNotFound(cluster_id=id)
            if issubclass(model, VnfClusterMember):
                raise vnfcluster.VnfClusterMemberNotFound(cluster_member_id=id)
            else:
                raise

    def _create_cluster_db(self, context, cluster_config):
        cluster_dict = self._create_cluster_pre(context, cluster_config)
        LOG.debug(_('cluster_dict %s'), cluster_dict)
        return cluster_dict

    def _get_cluster_db(self, context, cluster_id, fields=None):
        vnf_db = self._get_resource(context, VnfCluster, cluster_id)
        return self._make_cluster_dict(vnf_db, fields)

    def _get_clusters_db(self, context, filters=None, fields=None):
        return self._get_collection(context,
                                    VnfCluster,
                                    self._make_cluster_dict,
                                    filters=filters,
                                    fields=fields)

    def _delete_cluster_db(self, context, cluster_id):
        LOG.debug(_('Delete cluster_id %s'), cluster_id)
        with context.session.begin(subtransactions=True):
            vnfclustermember_db = context.session.query(VnfClusterMember).filter_by(
                cluster_id=cluster_id).first()
            if vnfclustermember_db is not None:
                raise nfvo.VnfClusterInUse(cluster_id=cluster_id)

            vnfcluster_db = self._get_resource(context, VnfCluster,
                                               cluster_id)
            context.session.delete(vnfcluster_db)

    def _create_cluster_pre(self, context, cluster_config):
        tenant_id = self._get_tenant_id_for_create(context, cluster_config)
        cluster_id = str(uuid.uuid4())
        name = cluster_config['name']
        description = cluster_config['description']
        vnfd_id = cluster_config['vnfd_id']
        policy_info = cluster_config['policy_info']

        with context.session.begin(subtransactions = True):
            cluster_db = VnfCluster(id = cluster_id,
                                    tenant_id = tenant_id,
                                    name = name,
                                    description = description,
                                    status = constants.ACTIVE,
                                    vnfd_id = vnfd_id,
                                    policy_info = policy_info)
            context.session.add(cluster_db)
        cluster_dict = self._make_cluster_dict(cluster_db)
        return cluster_dict

    def _make_cluster_dict(self, cluster_db, fields=None):
        res = {}
        key_list = ('id', 'tenant_id', 'name', 'description', 'status', 'vnfd_id',
                    'lb_id', 'policy_info',)
        res.update((key, cluster_db[key]) for key in key_list)
        return self._fields(res, fields)

    def _update_cluster_attr(self, context, cluster_id, field, attr):
        with context.session.begin(subtransactions=True):
            query = (self._model_query(context, VnfCluster).
                     filter(VnfCluster.id == cluster_id))
            query.update({field: attr})

    def _update_lb_policy(self, context, cluster_id, lb_result):
        with context.session.begin(subtransactions=True):
            query = (self._model_query(context, VnfCluster).
                     filter(VnfCluster.id == cluster_id))
            query.update({'policy_info': {'loadbalancer': lb_result}})

    def _update_policy_info(self, context, cluster_id, policy_info):
        with context.session.begin(subtransactions=True):
            query = (self._model_query(context, VnfCluster).
                     filter(VnfCluster.id == cluster_id))
            query.update({'policy_info': policy_info})

    def _update_lb_id(self, context, cluster_id, lb_id):
        with context.session.begin(subtransactions=True):
            query = (self._model_query(context, VnfCluster).
                     filter(VnfCluster.id == cluster_id))
            query.update({'lb_id': lb_id})

    def get_policy_attr(self, policy_info, key):
        attr = policy_info['properties'][key]
        return attr

    def get_lb_config(self, policy_info, attr_key):
        attr_dict= policy_info['properties']['load_balancer']['properties'][attr_key]
        return attr_dict

    #Cluster member related functions
    def _create_cluster_member(self, context, vnfm_plugin, cluster_dict, name, role):
        vnf_member = self._create_vnf_member(context, vnfm_plugin, cluster_dict, name)
        vnf_member['cp_id'] = self._get_member_cp_id(context, vnfm_plugin, cluster_dict, vnf_member['id'])
        member_dict = self._make_member_dict_from_vnf(cluster_dict['id'], role, vnf_member)
        self._create_member(context, member_dict)
        return member_dict

    def _create_vnf_member(self, context, vnfm_plugin, cluster, name):
        pre_vnf_dict = self._make_pre_vnf_dict(cluster, name)
        vnf_dict = vnfm_plugin.create_vnf(context, pre_vnf_dict)
        while (1):
            LOG.debug(_("Creating %s ..."), vnf_dict.get('name'))
            if vnf_dict.get('status') == 'ACTIVE':
                break
            time.sleep(2)
        return vnf_dict

    def _make_member_config(self, name, role, cluster_id, vnfd_id):
        config = {}
        config['name'] = name
        config['role'] = role
        config['cluster_id'] = cluster_id
        config['vnfd_id'] = vnfd_id
        member_config = {'clustermember': config}
        return member_config

    def _make_pre_vnf_dict(self, cluster, name):
        vnf_dict = {}
        p = {}
        p['description'] = 'A member of cluster ' + cluster['name']
        p['tenant_id'] = cluster['tenant_id']
        p['vim_id'] = ''
        p['name'] = name
        p['placement_attr'] = {}
        p['attributes'] = {}
        p['vnfd_id'] = cluster['vnfd_id']
        vnf_dict['vnf'] = p
        LOG.debug(_("_make_policy_dict p : %s"), p)
        return vnf_dict

    def _get_member_db(self, context, member_id, fields=None):
        member_db = self._get_resource(context, VnfClusterMember, member_id)
        return self._make_member_dict(member_db, fields)

    def _get_members_db(self, context, filters=None, fields=None):
        return self._get_collection(context, VnfClusterMember,
                                    self._make_member_dict,
                                    filters=filters, fields=fields)

    def _delete_member_db(self, context, member_id):
        with context.session.begin(subtransactions=True):
            member_db = self._get_resource(context, VnfClusterMember,
                                           member_id)
            context.session.delete(member_db)

    def _make_member_dict(self, member_db, fields=None):
        res = {}
        key_list = ('id', 'tenant_id', 'name', 'cluster_id', 'role', 'placement_attr', 'lb_member_id', 'cp_id')
        res.update((key, member_db[key]) for key in key_list)
        return self._fields(res, fields)

    def _create_member(self, context, member):
        member_name = member['name']
        member_id = member['id']
        tenant_id = member['tenant_id']
        cluster_id = member['cluster_id']
        role = member['role']
        cp_id = member['cp_id']
        placement_attr = member['placement_attr']
        with context.session.begin(subtransactions=True):
            member_db = VnfClusterMember(id=member_id,
                                         tenant_id=tenant_id,
                                         name=member_name,
                                         cluster_id=cluster_id,
                                         placement_attr=placement_attr,
                                         role=role,
                                         cp_id=cp_id)
            context.session.add(member_db)
        member_dict = self._make_member_dict(member_db)

        LOG.debug(_('cluster_member_dict %s'), member_dict)
        return member_dict

    def _make_member_dict_from_vnf(self, cluster_id, role, vnf_info):
        member_dict = {}
        member_dict['id'] = vnf_info['id']
        member_dict['tenant_id'] = vnf_info['tenant_id']
        member_dict['name'] = vnf_info['name']
        member_dict['cluster_id'] = cluster_id
        member_dict['role'] = role.upper()
        member_dict['placement_attr']=vnf_info['placement_attr']['vim_name']
        member_dict['cp_id'] = vnf_info['cp_id']
        LOG.debug(_("_make_cluster_member_dict c : %s"), member_dict)
        return member_dict

    def _get_member_cp_id(self, context, vnfm_plugin, cluster, member_id):
        vnf_resources = vnfm_plugin.get_vnf_resources(context, member_id)
        lb_targets = cluster['policy_info']['properties']['load_balancer']['properties']['targets']
        for resource in vnf_resources:
            if resource['name'] in lb_targets:
                member_port_id = resource['id']
                break
        return member_port_id

    def _get_member_by_role(self, context, cluster_id, role):
        member_db = (
            self._model_query(context, VnfClusterMember).
                filter(VnfClusterMember.cluster_id == cluster_id).
                filter(VnfClusterMember.role == role)).one()
        return member_db

    def get_members_by_attr(self, context, key=None, value=None):
        #filter by cluster_id
        member_list = self._get_members_db(context)
        if key != None and value != None:
            for mem in member_list:
                if mem[key] != value:
                    member_list.remove(mem)
        return member_list

    def update_member_role(self, context, vim_obj, lb_obj, member, new_role):
        member_id = member['id']
        if new_role == constants.CLUSTER_ACTIVE:
            cp_id = member['cp_id']
            lb_member_id = self._vim_drivers.invoke(vim_obj['type'], 'pool_member_add',
                                                    net_port_id=cp_id,
                                                    lb_info=lb_obj,
                                                    auth_attr=vim_obj['auth_cred'])
            self._update_member_attr(context, member_id, 'lb_member_id', lb_member_id)  # add STANDBY member to lb
            self._update_member_attr(context, member_id, 'role', new_role)  # Update from STANDBY to ACTIVE
        elif new_role == constants.CLUSTER_STANDBY:
            lb_member_id = member['lb_member_id']
            self._vim_drivers.invoke(vim_obj['type'], 'pool_member_remove',
                                     lb_id=lb_obj['loadbalancer'],
                                     pool_id=lb_obj['pool'],
                                     member_id=lb_member_id,
                                     auth_attr=vim_obj['auth_cred'])
            self._update_member_attr(context, member_id, 'lb_member_id', None)  # remove ACTIVE member from lb
            self._update_member_attr(context, member_id, 'role', new_role)

    def _update_member_attr(self, context, member_id, field, attr):
        with context.session.begin(subtransactions=True):
            query = (self._model_query(context, VnfClusterMember).
                     filter(VnfClusterMember.id == member_id))
            query.update({field: attr})