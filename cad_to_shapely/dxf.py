import os

import numpy as np  

from geomdl import NURBS, BSpline, utilities
import ezdxf
from ezdxf.addons import Importer
import ezdxf.entities as dxf 
import shapely.geometry as sg

from importer import CadImporter
from svg import _SvgPath 


class DxfImporter(CadImporter):

    def __init__(self,filename : str):
        super().__init__(filename)

    def _process_2d_polyline(self,polyline):
        xy = []
        polyline
        for i, location in enumerate(polyline.points()): 
            xy.append([location.x, location.y])
        
        if polyline.is_closed:    
            pl = sg.LinearRing(xy)
        else:
            pl = sg.LineString(xy)
        self.geometry.append(pl) 
        

    def _process_2d_spline(self,spline : dxf.Spline, delta = 0.1):
        """
        Uses geomdl module to create intermediate b-spline from dxf spline.
        This is then sampled as a linestring since shapely does not support splines. 
        """

        curve = NURBS.Curve()
        curve.degree = spline.dxf.degree
        curve.ctrlpts = spline.control_points
        
        curve.weights = [1] * spline.control_point_count()#spline.weights
        #curve.weights = spline.weights + [1] * np.array(spline.control_point_count()- len(spline.weights))
        curve.knotvector = spline.knots
 
        curve.delta = delta # TODO sampling - this could get out of hand depending on model dims and scale

        #TODO conditional delta: min length, n and check for straight lines

        xyz = np.array(curve.evalpts)
        xy = list([x[:-1] for x in xyz]) #remove z data

        pl = sg.LineString(xy)
        self.geometry.append(pl)
  

    def process(self, fillcolor = '#ff0000'):
        """
        implement superclass abstract method
        uses ezdxf to read dxf file and populate geometry
        """
        sdoc = ezdxf.readfile(self.filename)

        ents = sdoc.modelspace().query('CIRCLE LINE ARC POLYLINE ELLIPSE SPLINE SHAPE')
        n_splines = n_polylines = 0
        for e in ents:
            if isinstance(e, dxf.Spline) and e.dxf.flags >= ezdxf.lldxf.const.PLANAR_SPLINE:
                self._process_2d_spline(e)
                n_splines +=1
            elif isinstance(e, dxf.Polyline):
                if e.get_mode() == 'AcDb2dPolyline':
                    self._process_2d_polyline(e)
                    n_polylines += 1
                else:
                    pass

        return 'Found {} polylines and {} splines'.format(n_polylines,n_splines)
 