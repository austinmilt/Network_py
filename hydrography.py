# This is the main file that defines classes to create a hydrology network
#   with barriers, linked classes and attributes

# Created 11/23/2015
# Updated 11/23/2015
# Author: Austin Milt
# ArcGIS version: 10.3.1
# Python version: 2.7.8

## basin

    ## lake
    
    ## catchment
    
    ## hydrology network

        ## tributary network
        
            ## reach
        
            ## structure (dam, rsx)
            

# ~~ GLOBAL CONSTANTS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# OrderedObject
ORD_DID = 0

# Structure
STR_FPR = 0.0

# Barrier
BAR_PAS = 0.0 # default passability for undefined fishes/guilds

# load_data()
LOD_DAT_BAR = 'barriers'
LOD_DAT_FLO = 'flowlines'
LOD_FLD_BID = 'BID'
LOD_FLD_BDS = 'BID_DS'
LOD_FLD_RID = 'RID'
LOD_FLD_NAT = 'NATION'
LOD_FLD_LAK = 'LAKE'
LOD_FLD_FPR = 'F_PROP'
LOD_FLD_HAB = 'HAB_UP'
LOD_FLD_CST = 'COST'
LOD_FLD_LAM = 'lamp_oid'
LOD_FLD_P04 = 'PASS04'
LOD_FLD_P07 = 'PASS07'
LOD_FLD_P10 = 'PASS10'
LOD_FLD_RDS = 'RID_DS'
LOD_FLD_TID = 'TID'
LOD_FLD_CAT = 'HydroID'
LOD_FLD_WSA = 'WSAKM2'
LOD_FLD_LEN = 'Shape_Length'
LOD_VAL_SLF = -1



# ~~ ORDERED OBJECT ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class OrderedObject:
    """
    Basic hydrologic object with one downstream OrderedObject and at least one
    upstream OrderedObject.
    """
    
    def __init__(self, id=ORD_DID, **attributes):
        
        # set attributes using defaults and user overrides
        P = {
            'down': self, # next downstream OrderedObjects
        }
        P['id'] = id
        P.update(dict((k.lower(), attributes[k]) for k in attributes))
        for k in P: setattr(self, k, P[k])
            

    def trace_down(self, levels=None, types=None):
        """
        Traces downstream of this Structure and returns all downstream
        Structures
        
        INPUTS:
            levels  = (optional) number of levels to trace downstream. Default
                (None) is all levels until the last object is reached.
                
            types   = (optional) list, set, or tuple of types to return. Can 
                be any type with OrderedObject parent class. Default is any 
                OrderedObject
                
        OUTPUTS: ordered list of all downstream OrderedObjects
        """
        if types is None: types = OrderedObject
        types = tuple(types)
        curObj = self
        downstreamObjects = []
        count = 0
        while (curObj.down is not curObj) and any((count < levels, levels is None)):
            count += 1
            if isinstance(curObj.down, types):
                downstreamObjects.append(curObj.down)
            curObj = curObj.down
            
        return downstreamObjects
        
        
    def __setattr__(self, attribute, value):
    
        # error checking
        if attribute == 'down':
            if not isinstance(value, OrderedObject):
                raise TypeError('Downstream objects must be a sub-class of OrderedObject.')
                
        # handle other attribute assignments
        self.__dict__[attribute] = value
        
        
    def __repr__(self):
        return '%s %s' % (self.__class__.__name__, str(self.id))
        
        
        
# ~~ ORDERED COLLECTION ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class OrderedCollection(OrderedObject):
    """
    OrderedCollection is a collection of OrderedObjects with methods to contain
    and trace along elements.
    """

    def __init__(self, objects):
    
        OrderedObject.__init__(self)
        
        # add objects to the set
        self.objects = set()
        for obj in objects:    
            if not isinstance(obj, OrderedObject):
                raise TypeError('OrderedCollections can only contain OrderedObjects.')
            self.objects.add(obj)
        self.first_up()
    
    
    def first_up(self):
        """
        Initializes upstream tracing by finding the set of nearest upstream
        objects for each object. Sets the self.up dictionary in place.
        """
        self.__dict__['up'] = {}
        for obj in self.objects:
            if obj not in self.up: self.up[obj] = set()
            if obj.down not in self.up: self.up[obj.down] = set()
            if obj.down is not obj: self.up[obj.down].add(obj)
        
    
    def trace_up(self, startingObject, levels=None, types=(OrderedObject,)):
        """
        Traces upstream from an object to all its upstream objects of a
        specified type.
        
        INPUTS:
            levels  = (optional) number of levels to trace upstream. Default
                (None) is all levels until the first object is reached.
                
            types   = (optional) list, set, or tuple of types to return. Can 
                be any type with OrderedObject parent class. Default is any 
                OrderedObject
                
        OUTPUTS: set of all upstream objects of the starting object
        """
        toTrace = [(obj, 0) for obj in self.up[startingObject]]
        upstreamObjects = set()
        while (len(toTrace) > 0) and any((toTrace[0][1] < levels, levels is None)):
            obj, level = toTrace.pop(0)
            if isinstance(obj, types):
                upstreamObjects.add(obj)
                
            # update remaining trace list
            toTrace.extend([(newObj, level+1) for newObj in self.up[obj]])
        
        return upstreamObjects
        
        
    def __setattr__(self, attribute, value):
        
        if attribute == 'up':
            print 'Use the first_up() method to set the up{} dictionary.'
        
        else:
            self.__dict__[attribute] = value
        
    
    
# ~~ STRUCTURE ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #            
class Structure(OrderedObject):
    """
    Structure is a stationary structure in a water body with hydrologic
    properties.
    """
    
    def __init__(self, **attributes):
    
        OrderedObject.__init__(self)
        
        # set attributes using defaults and user overrides
        P = {
            'fprop': STR_FPR, # proportion along reach
            'reach': None, # Reach object on which self is found
            'country': None # country in which self is found
        }
        P.update(dict((k.lower(), attributes[k]) for k in attributes))
        for attribute in P:
            setattr(self, attribute, P[attribute])

            

# ~~ BARRIER ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class Barrier(Structure):
    """
    Barriers are one type of Structure that create impediments to fish
    movement.
    """
    
    def __init__(self, **attributes):
        Structure.__init__(self)
        
        # set attributes using defaults and user overrides
        P = {
            'pass': {} # dictionary where keys are fish/guilds and values are passabilities
        }
        P.update(dict((k.lower(), attributes[k]) for k in attributes))
        for attribute in P:
            setattr(self, attribute, P[attribute])


# ~~ DAM ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class Dam(Structure):
    """
    Dams are one type of Structure with built in dimensional and removal cost
    attributes.
    """
    pass
    
            
        
        
# ~~ load_data() ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def load_data(database, **options):
    """
    LOAD_DATA() loads hydrography data from an mdb Access database using arcpy
    and converts it into the format for create_hydrography().
    
    INPUT:
        database    = path to database file
        
        **options   = optional keyword arguments. Value arguments are:
        
            barriers: name of the barriers dataset in the database. Default is
                LOD_DAT_BAR
            flowlines: name of the flowlines dataset in the database. Default
                LOD_DAT_FLO
            bid_field: unique barrier ID field in barriers dataset. Default is
                LOD_FLD_BID
            bds_field: barrier downstream ID field in barriers dataset. Default
                is LOD_FLD_BDS
            rid_field: flowline ID field in barriers and flowlines dataset. 
                Default is LOD_FLD_RID
            nat_field: country of location of barrier in barriers dataset.
                Default is LOD_FLD_NAT
            lak_field: lake of catchment in which barrier is located in
                barriers dataset. Default is LOD_FLD_LAK
            fpr_field: proportion along flowline field in barriers dataset.
                Default is LOD_FLD_FPR
            hab_field: upstream habitat field in barriers dataset. Default is
                LOD_FLD_HAB
            cst_field: cost of barrier removal field in barriers dataset.
                Default is LOD_FLD_CST
            lam_field: lamprey first barrier ID field in barriers dataset.
                Default is LOD_FLD_LAM
            low_field: low-passability field in barriers dataset. Default is
                LOD_FLD_P04
            mid_field: mid-passability field in barriers dataset. Default is
                LOD_FLD_P07    
            hih_field: high-passability field in barriers dataset. Default is
                LOD_FLD_P10
            rds_field: flowline ID field of next downstream flowline in 
                flowlines dataset. Default is LOD_FLD_RDS
            tid_field: tributary ID field in flowlines dataset.
                Default is LOD_FLD_TID
            cat_field: catchment ID field in flowlines dataset. Default is 
                LOD_FLD_CAT
            wsa_field: flowline's watershed area field in flowlines dataset.
                Default is LOD_FLD_WSA
            len_field: flowline's length field in flowlines dataset. Default
                is LOD_FLD_LEN
    """
    pass
    
    ## flowlines's watershed area is same as catchment's total area in km2
    ## can total trib length from all flowline lengths along trib
    ## 
            
            
            
# ~~ create_hydrography() ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def create_hydrography(data):
    """
    Creates a Hydrography object from formatted data.
    
    INPUTS:
        data    = formatted hydrography data as returned by load_data()
        
    OUTPUTS: Hydrography object with hydrography sub-objects in the network.
    """
    pass
    
    

if __name__ == '__main__':

    pass
    
    ## load the database
    ## pass into create_hydrography
    import pdb; pdb.set_trace()
