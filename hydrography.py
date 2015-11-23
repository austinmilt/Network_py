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
    
    def __init__(self, **attributes):
        
        # set attributes using defaults and user overrides
        P = {
            'up': set(), # set of next upstream OrderedObjects
            'down': self # next downstream OrderedObjects
        }
        P.update(dict((k.lower(), attributes[k]) for k in attributes))
        setattr(self, 'up', P['up'])
        setattr(self, 'down', P['down'])
            

    def trace_up(self, types=set()):
        """
        Traces upstream of this OrderedObject and returns all upstream 
        OrderedObjects.
        
        INPUTS:
            types   = list, set, or tuple of types to return. Can be any type 
                with OrderedObject parent class
                
        OUTPUTS: set() of all upstream OrderedObjects
        """
        types = tuple(types)
        upstreamObjects = set()
        toTrace = set()
        toTrace.update(self.up)
        while len(toTrace) > 0:
            curObj = toTrace.pop()
            if isinstance(curObj, types):
                upstreamObjects.add(curObj)
            toTrace.update(curObj.up)
            
        return upstreamObjects
        
    
    def trace_down(self, types=set()):
        """
        Traces downstream of this Structure and returns all downstream
        Structures
        
        INPUTS:
            types   = list, set, or tuple of types to return. Can be any type 
                with Structure parent class
                
        OUTPUTS: ordered list of all downstream structures
        """
        types = tuple(types)
        curObj = self
        downstreamObjects = []
        while curObj.down is not curObj:
            if isinstance(curObj.down, types):
                downstreamObjects.append(curObj.down)
            curObj = curObj.down
            
        return downstreamObjects
        
        
    def __setattr__(self, attribute, value):
    
        # update properties of downstream object and self
        if attribute == 'down':
            self.__dict__['down'] = value
            if value is not None:
                if not isinstance(value, OrderedObject):
                    raise TypeError('Downstream objects must be a sub-class of OrderedObject.')
                value.up.add(self)
                
        # handle other attributes
        self.__dict__[attribute] = value


    
# ~~ STRUCTURE ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #            
class Structure(OrderedObject):
    """
    Structure is a stationary structure in a water body with hydrologic
    properties.
    """
    
    def __init__(self, **attributes):
        
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
        super(Barrier, self).__init__()
        
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
