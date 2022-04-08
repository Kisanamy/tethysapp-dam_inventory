from argparse import Namespace
from tethys_sdk.base import TethysAppBase, url_map_maker
from tethys_sdk.app_settings import CustomSetting
from tethys_sdk.app_settings import PersistentStoreDatabaseSetting
from tethys_sdk.permissions import Permission, PermissionGroup
from tethys_sdk.app_settings import SpatialDatasetServiceSetting


class DamInventory(TethysAppBase):
    """
    Tethys app class for Dam Inventory.
    """

    name = 'Dam By Liriel'
    index = 'dam_inventory:home'
    icon = 'dam_inventory/images/icon.gif'
    package = 'dam_inventory'
    root_url = 'dam-inventory'
    color = '#1a1a1a'
    description = 'Dam Inventory'
    tags = 'Reference Timeseries'
    enable_feedback = False
    feedback_emails = []
    index_layer = 0

    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        url_maps = (
            UrlMap(
                name='home',
                url='dam-inventory',
                controller='dam_inventory.controllers.home'
            ),
            UrlMap(
                name='add_dam',
                url='dam-inventory/dams/add',
                controller='dam_inventory.controllers.add_dam'
            ),
            UrlMap(
                name='dams',
                url='dam-inventory/dams',
                controller='dam_inventory.controllers.list_dams'
            ),
            UrlMap(
                name='assign_hydrograph',
                url='dam-inventory/hydrographs/assign',
                controller='dam_inventory.controllers.assign_hydrograph'
            ),
            UrlMap(
                name='hydrograph',
                url='dam-inventory/hydrographs/{hydrograph_id}',
                controller='dam_inventory.controllers.hydrograph'
            ),
            UrlMap(
                name='hydrograph_ajax',
                url='dam-inventory/hydrographs/{dam_id}/ajax',
                controller='dam_inventory.controllers.hydrograph_ajax'
            ),
            UrlMap(
                name='delete_dam',
                url='dam-inventory/dams/{dam_id}/delete',
                controller='dam_inventory.controllers.delete_dam'
            ),
            UrlMap(
                name='import_dams',
                url='dam-inventory/import_dams',
                controller='dam_inventory.controllers.import_dams'
            ),
        )

        return url_maps

    def custom_settings(self):
        """
        Example custom_settings method.
        """
        custom_settings = (
            CustomSetting(
                name='max_dams',
                type=CustomSetting.TYPE_INTEGER,
                description='Maximum number of dams that can be created in the app.',
                required=False
            ),
        )
        return custom_settings
    
    def persistent_store_settings(self):
        """
        Define Persistent Store Settings.
        """
        ps_settings = (
            PersistentStoreDatabaseSetting(
                name='primary_db',
                description='primary database',
                initializer='dam_inventory.model.init_primary_db',
                required=True
            ),
        )

        return ps_settings
    
    def spatial_dataset_service_settings(self):
        """
        Example spatial_dataset_service_settings method.
        """
        sds_settings = (
            SpatialDatasetServiceSetting(
                name='main_geoserver',
                description='spatial dataset service for app to use',
                engine=SpatialDatasetServiceSetting.GEOSERVER,
                required=True,
            ),
        )

        return sds_settings

    def permissions(self):
        """
        Define permissions for the app.
        """
        add_dams = Permission(
            name='add_dams',
            description='Add dams to inventory'
        )   

        admin = PermissionGroup(
            name='admin',
            permissions=(add_dams,)
        )

        permissions = (admin,)

        return permissions