# from functools import _Descriptor
# from typing_extensions import TypeGuard
from django.db import models
from django.db.models.fields import CharField
import datetime
from django.db.models.signals import post_delete, post_save
from django.dispatch.dispatcher import receiver
import os
import zipfile
from fiona import crs
import geopandas as gpd 
from shapely import geometry
from sqlalchemy import *
from geoalchemy2 import Geometry, WKTElement
import glob
from osgeo import gdal
import pyproj
from shapely.geometry import Polygon, Point, LineString

# import warnings
# warnings.filterwarnings('ignore')

# Import the library
from geo.Geoserver import Geoserver
from geo.Postgres import Db

# Initialize the library
db = Db(dbname='geoApp', user='postgres',
        password='1234', host='localhost', port=5432)
geo = Geoserver('http://127.0.0.1:8081/geoserver', username='admin', password='geoserver')


# Shapefile model
class Shp(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=1500, blank=True)
    file = models.FileField(upload_to='%Y/%M/%D')
    uploaded_date = models.DateField(default=datetime.date.today, blank=True)

    def __str__(self):
        return self.name

# receiving signal
@receiver(post_save, sender=Shp)
def publish_data(sender, instance, created, **kwargs):
    file = instance.file.path
    file_format = os.path.basename(file).split('.')[-1]
    file_name = os.path.basename(file).split('.')[0]
    file_path = os.path.dirname(file)
    name = instance.name
    conn_str = 'postgresql://postgres:1234@localhost:5432/geoApp'

    # Extract zipfile
    with zipfile.ZipFile(file, 'r') as zip_ref:
        zip_ref.extractall(file_path)

    # Remove ZipFile
    os.remove(file)

    shp = glob.glob(r'{}/**/*.shp'.format(file_path),
                    recursive=True)[0]  # to get shp
    gdf = gpd.read_file(shp)  # make geodataframe
    crs_name = str(gdf.crs['init'])
    epsg = int(crs_name.replace('epsg:', ' '))
    if epsg is None:
        epsg = 4326  # WGS84 coordinate system

    geom_type = gdf.geom_type[1]

    engine = create_engine(conn_str)  # Creating SQLACHEMY'S ENGINE TO USE
    gdf['geom'] = gdf['geometry'].apply(lambda x: WKTElement(x.wkt, srid=epsg))

    # DROPPING THE GEOMETRY COLUMN (SINCE IT IS ALREADY BACKED UP WITH GEOM COLUMN)
    gdf.drop('geometry', axis=1, inplace=True)

    gdf.to_sql(name, engine, 'data', if_exists='replace', index=False, dtype={
               'geom': Geometry('Geometry', srid=epsg)})  # print post to postgresql

    os.remove(shp)

    


    ''' Publishing shapefile to geoserver using geoserver-rest'''
    geo.create_workspace(workspace='geoApp1')
    # For creating postGIS connection and publish postGIS table
    geo.create_featurestore(store_name='geoApp', workspace='geoApp', db='geoApp', host='localhost', pg_user='postgres',
                        pg_password='1234', schema='data')

    geo.publish_featurestore(workspace='geoApp', store_name='geoApp', pg_table=name)

    geo.create_outline_featurestyle('geoApp_shp', workspace='geoApp')

    geo.publish_style(layer_name='name', style_name='geoApp_shp', workspace='geoApp')


@receiver(post_delete, sender=Shp)


def delete_data(sender, instance, **kwargs):
    db.delete_table( schema='data', table_name=instance.name)
    geo.delete_layer(instance.name, 'geoApp')
