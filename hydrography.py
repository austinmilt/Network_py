# This is the main file that defines classes to create a hydrology network
#   with barriers, linked classes and attributes

# Created 11/23/2015
# Updated 11/25/2015
# Author: Austin Milt
# ArcGIS version: 10.3.1
# Python version: 2.7.8
            

# ~~ GLOBAL CONSTANTS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# OrderedObject
ORD_DID = 0

# Reach
RCH_LEN = None
RCH_SIZ = None

# Structure
STR_FPR = 0.0

# Barrier
BAR_CST = None

# Dam
DAM_WID = None
DAM_LEN = None
DAM_HIT = None

# RSX
RSX_WID = None
RSX_LEN = None
RSX_DRP = None

# OrderedCollection

# Catchment
CAT_ARE = None

# load_data()
LOD_DAT_BAR = 'barriers'
LOD_DAT_FLO = 'flowlines'
LOD_DAT_CAT = 'catchments'
LOD_DAT_TRB = 'tributaries'
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
LOD_FLD_CDS = 'HydroID_DS'
LOD_FLD_WSA = 'WSAKM2'
LOD_FLD_LEN = 'Shape_Length'
LOD_FLD_STO = 'STRAHLER'
LOD_VAL_SLF = -1

# create_hydrography()
CRH_DAT_BAR = 'barriers'
CRH_DAT_FLO = 'flowlines'
CRH_DAT_CAT = 'catchments'
CRH_DAT_TRB = 'tributaries'
CRH_FLD_BID = 'bid'
CRH_FLD_BDS = 'bds'
CRH_FLD_RID = 'rid'
CRH_FLD_NAT = 'nation'
CRH_FLD_LAK = 'lake'
CRH_FLD_FPR = 'fprop'
CRH_FLD_HAB = 'habitat'
CRH_FLD_CST = 'cost'
CRH_FLD_LAM = 'lamp'
CRH_FLD_P04 = 'passlow'
CRH_FLD_P07 = 'passmid'
CRH_FLD_P10 = 'passhigh'
CRH_FLD_RDS = 'rds'
CRH_FLD_TID = 'tid'
CRH_FLD_CAT = 'cid'
CRH_FLD_CDS = 'cds'
CRH_FLD_WSA = 'area'
CRH_FLD_LEN = 'length'
CRH_FLD_STO = 'size'


# ########################################################################### #
# ########################## SINGLE UNITS ################################### #
# ########################################################################### #

# ~~ ORDERED OBJECT ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class OrderedObject(object):
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
        

    def __eq__(self, other):
        if self is other: return True
        else: return False
            

    def trace_down(self, levels=None, filters=None, types=None):
        """
        Traces downstream of this object and returns all downstream
        objects
        
        INPUTS:
            levels  = (optional) number of levels to trace downstream. Default
                (None) is all levels until the last object is reached.
                
            filters = (optional) like levels, but stops after attributes
                of upstream objects no longer match the filter. Supply as
                a dict of attribute names with filter values as values. Default
                (None) is no filter.
                
            types   = (optional) list, set, or tuple of types to return. Can 
                be any type with OrderedObject parent class. Default is any 
                OrderedObject
                
        OUTPUTS: ordered list of all downstream OrderedObjects
        """
        
        
        # define filter test
        def filter_test(obj):
            if filters is None: return True
            return all([obj.__dict__[k] == filters[k] for k in filters])
        
        # trace down
        if types is None: types = OrderedObject
        if not hasattr(types, '__iter__'): types = (types,)
        curObj = self
        downstreamObjects = []
        count = 0
        while (curObj.down is not curObj) and any((count < levels, levels is None)) and filter_test(curObj.down):
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
        
    
    
# ~~ STRUCTURE ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #            
class Structure(OrderedObject):
    """
    Structure is a stationary structure in a water body with hydrologic
    properties.
    """
    
    def __init__(self, **attributes):
    
        OrderedObject.__init__(self, **attributes)
        
        # set attributes using defaults and user overrides
        P = {
            'fprop': STR_FPR, # proportion along reach
            'reach': None, # Reach object on which self is found
            'country': None, # country in which self is found
            'tributary': None # tributary along which self is found
        }
        P.update(dict((k.lower(), attributes[k]) for k in attributes))
        for attribute in P:
            setattr(self, attribute, P[attribute])
        
        
    def __setattr__(self, attribute, value):
    
        super(Structure, self).__setattr__(attribute, value)
        
        if attribute == 'fprop':
            if (value < 0) or (value > 1):
                raise ValueError('fprop attribute must be between 0 and 1.')
            
        self.__dict__[attribute] = value
        
        
            
# ~~ BARRIER ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class Barrier(Structure):
    """
    Barriers are one type of Structure that create impediments to fish
    movement.
    """
    
    def __init__(self, **attributes):
        Structure.__init__(self, **attributes)
        
        # set attributes using defaults and user overrides
        P = {
            'passabilities': {}, # dictionary where keys are fish/guilds and values are passabilities
            'cost': BAR_CST # cost of making barrier totally passable (be e.g. removal)
        }
        P.update(dict((k.lower(), attributes[k]) for k in attributes))
        for attribute in P:
            setattr(self, attribute, P[attribute])

    
    def __setattr__(self, attribute, value):
        
        super(Barrier, self).__setattr__(attribute, value)
        
        if attribute == 'passabilities':
            for k in value:
                if (value[k] < 0) or (value[k] > 1):
                    raise ValueError('passabilities must be between 0 and 1.')
            
        self.__dict__[attribute] = value

        
        
# ~~ DAM ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class Dam(Barrier):
    """
    Dams are one type of Barrier with built in dimensional attributes.
    """
    
    def __init__(self, **attributes):
        Barrier.__init__(self, **attributes)
    
        # set attributes using defaults and user overrides
        P = {
            'width': DAM_WID, # up- to down-stream width of dam
            'height': DAM_HIT, # vertical height of dam
            'length': DAM_LEN # river spanning length of dam
        }
        P.update(dict((k.lower(), attributes[k]) for k in attributes))
        for attribute in P:
            setattr(self, attribute, P[attribute])
    
    
    def __setattr__(self, attribute, value):
    
        super(Dam, self).__setattr__(attribute, value)
        
        if attribute in ('width', 'height', 'length'):
            if (value is not None) and (value < 0):
                raise ValueError('Dam dimensions must be non-negative.')
    
    
        self.__dict__[attribute] = value
        
        
        
# ~~ RSX ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class RSX(Barrier):
    """
    RSX are road stream crossings and are one type of Barrier with built in 
    dimensional attributes.
    """
    
    def __init__(self, **attributes):
        Barrier.__init__(self, **attributes)
    
        # set attributes using defaults and user overrides
        P = {
            'width': RSX_WID, # up- to down-stream width of road
            'drop': RSX_DRP, # vertical height of dam
            'length': RSX_LEN # river spanning length of rsx
        }
        P.update(dict((k.lower(), attributes[k]) for k in attributes))
        for attribute in P:
            setattr(self, attribute, P[attribute])
    
    
    def __setattr__(self, attribute, value):
        
        super(RSX, self).__setattr__(attribute, value)
        
        if attribute in ('width', 'drop', 'length'):
            if (value is not None) and (value < 0):
                raise ValueError('RSX dimensions must be non-negative.')
    
    
        self.__dict__[attribute] = value
            

            
# ########################################################################### #
# ########################### COLLECTIONS ################################### #
# ########################################################################### #

# ~~ ORDERED COLLECTION ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class OrderedCollection(OrderedObject):
    """
    OrderedCollection is a collection of OrderedObjects with methods to contain
    and trace along elements.
    """

    def __init__(self, objects, **attributes):
    
        OrderedObject.__init__(self, **attributes)
        
        # add objects to the set
        self.objects = set()
        for obj in objects:    
            if not isinstance(obj, OrderedObject):
                raise TypeError('OrderedCollections can only contain OrderedObjects.')
            self.objects.add(obj)
        self.first_up()
        
        
    def __setattr__(self, attribute, value):
        
        super(OrderedCollection, self).__setattr__(attribute, value)
        
        if attribute == 'up':
            print 'Use the first_up() method to set the up{} dictionary.'
        
        else:
            self.__dict__[attribute] = value

    
    def first_up(self, upAttr='up', objectAttr='objects'):
        """
        Initializes upstream tracing by finding the set of nearest upstream
        objects for each object. Sets the up dictionary in place.
        
        INPUTS:
            upAttr  = (optional) attribute name for the first_up dictionary.
                Default is 'up'. Used for OrderedCollections with more than
                one set of OrderedObjects.
                
            objectAttr = (optional) attribute name of the objects to perform
                calculations on. Default is 'objects'. Used for 
                OrderedCollections with more than one set of OrderedObjects.
                
        OUTPUTS: nothing. Modified in-place
        """
        self.__dict__[upAttr] = {}
        up = self.__dict__[upAttr]
        for obj in self.__dict__[objectAttr]:
            if obj not in up: up[obj] = set()
            if obj.down not in up: up[obj.down] = set()
            if obj.down is not obj: up[obj.down].add(obj)
        
    
    def trace_up(
        self, startingObject, levels=None, filters=None, 
        types=(OrderedObject,), upAttr='up'
        
    ):
        """
        Traces upstream from an object to all its upstream objects of a
        specified type.
        
        INPUTS:
            levels  = (optional) number of levels to trace upstream. Default
                (None) is all levels until the first object is reached.
                
            filters = (optional) like levels, but stops after attributes
                of upstream objects no longer match the filter. Supply as
                a dict of attribute names with filter values as values. Default
                (None) is no filter.
                
            types   = (optional) list, set, or tuple of types to return. Can 
                be any type with OrderedObject parent class. Default is any 
                OrderedObject
                
            upAttr  = (optional) attribute name for the first_up dictionary.
                Default is 'up'. Used for OrderedCollections with more than
                one set of OrderedObjects.
                
        OUTPUTS: set of all upstream objects of the starting object
        """
        
        # define filter test
        def filter_test(obj):
            if filters is None: return True
            return all([obj.__dict__[k] == filters[k] for k in filters])
        
        # trace
        up = self.__dict__[upAttr]
        toTrace = [(obj, 0) for obj in up[startingObject] if filter_test(obj)]
        upstreamObjects = set()
        while (len(toTrace) > 0) and any((toTrace[0][1] < levels, levels is None)):
            obj, level = toTrace.pop(0)
            if isinstance(obj, types):
                upstreamObjects.add(obj)
                
            # update remaining trace list
            toTrace.extend([(newObj, level+1) for newObj in up[obj] if filter_test(obj)])
        
        return upstreamObjects
        
        
    @staticmethod
    def __operate_over__(objects, attribute, operation='+', ignoreNone=True):
        """
        Operates over the attribute of the objects in the list, optionally 
        ignoring objects with an undefined attribute.
        
        INPUTS:
            objects     = list or set of objects to operate over
            
            attribute   = attribute of the objects from which values are used
                in operation
                
            operation   = (optional) operation to perform. Currently supported
                operations are '+' for addition and '*' for multiplication.
                
            ignoreNone  = (optional) flag to indicate to skip (True) objects
                when they dont have the attribute defined versus failing
                (False)
                
        OUTPUTS: result of the operation
        """
        ignoreTest = lambda x: ignoreNone or (x is not None)
        values = [obj.__dict__[attribute] for obj in objects]
        if operation == '+':
            return sum(values)
        elif operation == '*':
            prod = 1.
            for v in values: prod *= v
            return prod
    


# ~~ REACH ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class Reach(OrderedCollection):
    """
    Reach is a segment of river and collects barriers.
    """
    
    def __init__(self, barriers=set(), **attributes):
        OrderedCollection.__init__(self, barriers, **attributes)
    
        # set attributes using defaults and user overrides
        P = {
            'length': RCH_LEN, # reach segment length
            'size': RCH_SIZ, # reach size (stream order)
            'catchment': None, # Catchment in which self is found
            'tributary': None # Tributary in which self is found
        }
        P.update(dict((k.lower(), attributes[k]) for k in attributes))
        for attribute in P:
            setattr(self, attribute, P[attribute])
            
        # assign barriers their reach
        self.barriers = self.objects
        for barrier in self.barriers:
            barrier.reach = self

    
    
    
# ~~ CATCHMENT ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class Catchment(OrderedCollection):
    """
    Catchment is an OrderedCollection for reaches within a tributary, where
    reaches start and end within the catchment.
    """
    
    def __init__(self, reaches=set(), **attributes):
        
        OrderedCollection.__init__(self, reaches, **attributes)
        
        # set attributes using defaults and user overrides
        P = {
            'area': CAT_ARE, # watershed drainage area of self
            'tributary': None # Tributary along which self is located
        }
        P.update(dict((k.lower(), attributes[k]) for k in attributes))
        for attribute in P:
            setattr(self, attribute, P[attribute])
        
        # update reach catchment identity
        self.reaches = self.objects
        for reach in self.reaches: reach.catchment = self
        
        
    def length_all(self, ignoreNone=True):
        """
        Calculates the total length of reaches within the catchment, optionally 
        ignoring reaches with an undefined length.
        """
        return self.__operate_over__(self.reaches, 'length', '+', ignoreNone)
        
        
    def length_up(self, reach, levels=None, ignoreNone=True):
        """
        Calculates the length of the Tributary upstream of the given reach
        within the catchment, optionally ignoring reaches with an undefined
        length.
        
        INPUTS:
            reach       = starting reach to calculate upstream length from
            levels      = (optional) see OrderedCollection.trace_up()
            ignoreNone  = (optional) whether to skip (True) when encountering
                reaches with an undefined length. Default is True.
                
        OUTPUTS: float of the total length upstream of the reach
        """
        upstreamReaches = self.trace_up(
            reach, levels, filters={'catchment': self}, types=Reach
        )
        return self.__operate_over__(upstreamReaches, 'length', '+', ignoreNone)
        
        
    def length_down(self, reach, levels=None, ignoreNone=True):
        """
        Calculates the length of the Tributary downstream of the given reach
        within the catchment, optionally ignoring reaches with an undefined 
        length.
        
        INPUTS:
            reach       = starting reach to calculate downstream length from
            levels      = (optional) see OrderedObject.trace_down()
            ignoreNone  = (optional) whether to skip (True) when encountering
                reaches with an undefined length. Default is True.
                
        OUTPUTS: float of the total length downstream of the reach
        """
        downstreamReaches = reach.trace_down(
            levels, filters={'catchment': self}, types=Reach
        )
        return self.__operate_over__(downstreamReaches, 'length', '+', ignoreNone)

        
        
        
# ~~ TRIBUTARY ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class Tributary(OrderedCollection):
    """
    Tributary is a collection of reaches that spans catchments and drains
    into a lake.
    """
    
    def __init__(self, reaches, **attributes):
        
        OrderedCollection.__init__(self, reaches, **attributes)
        
        # set attributes using defaults and user overrides
        P = {
            'lake': None, # lake into which self drains
        }
        P.update(dict((k.lower(), attributes[k]) for k in attributes))
        for attribute in P:
            setattr(self, attribute, P[attribute])
        
        # update catchment tributary identity and assign catchments for self
        self.reaches = self.objects
        self.catchments = set()
        self.barriers = set()
        for reach in self.reaches:
            reach.catchment.tributary = self
            self.catchments.add(reach.catchment)
            reach.tributary = self
            
            for barrier in reach.barriers:
                barrier.tributary = self
                self.barriers.add(barrier)
            
        # update the first upstream object dictionaries
        del self.up
        self.first_up('catchUp', 'catchments')
        self.first_up('reachUp', 'reaches')
        self.first_up('barUp', 'barriers')
            
            
    def trace_up(self, startingObject, levels=None, filters=None):
        """
        See OrderedCollection.trace_up, except types and upAttr are
        automatically determined.
        """
        if isinstance(startingObject, Reach):
            return super(Tributary, self).trace_up(startingObject, levels, filters, (Reach,), 'reachUp')
            
        elif isinstance(startingObject, Catchment):
            return super(Tributary, self).trace_up(startingObject, levels, filters, (Catchment,), 'catchUp')
        
        elif isinstance(startingObject, Structure):
            return super(Tributary, self).trace_up(startingObject, levels, filters, (Structure,), 'barUp')
            
    
    def area_all(self, ignoreNone=True):
        """
        Calculates the total area of catchements the tributary spans, optionally 
        ignoring catchments with an undefined area.
        """
        return self.__operate_over__(self.catchments, 'area', '+', ignoreNone)
        
        
    def area_up(self, catchment, levels=None, ignoreNone=True):
        """
        Calculates the area of the catchments upstream of the given catchment
        the tributary spans, optionally ignoring reaches with an undefined
        length.
        
        INPUTS:
            catchment   = starting catchment to calculate upstream area from
            levels      = (optional) see OrderedCollection.trace_up()
            ignoreNone  = (optional) whether to skip (True) when encountering
                catchments with an undefined area. Default is True.
                
        OUTPUTS: float of the total area upstream of the catchment
        """
        upstreamCatchments = self.trace_up(
            catchment, levels, filters={'tributary': self}
        )
        return self.__operate_over__(upstreamCatchments, 'area', '+', ignoreNone)
        
        
    def area_down(self, catchment, levels=None, ignoreNone=True):
        """
        Calculates the area of the catchments downstream of the given catchment
        the tributary spans, optionally ignoring catchments with an undefined 
        area.
        
        INPUTS:
            catchment       = starting reach to calculate downstream length from
            levels      = (optional) see OrderedObject.trace_down()
            ignoreNone  = (optional) whether to skip (True) when encountering
                reaches with an undefined length. Default is True.
                
        OUTPUTS: float of the total length downstream of the reach
        """
        downstreamCatchments = catchment.trace_down(
            levels, filters={'tributary': self}, types=Catchment
        )
        return self.__operate_over__(downstreamCatchments, 'area', '+', ignoreNone)
        
        
    def length_all(self, ignoreNone=True):
        """
        Calculates the total length of reaches within the tributary, optionally 
        ignoring reaches with an undefined length.
        """
        return self.__operate_over__(self.reaches, 'length', '+', ignoreNone)
        
        
    def length_up(self, reach, levels=None, ignoreNone=True):
        """
        Calculates the length of the Tributary upstream of the given reach
        within the tributary, optionally ignoring reaches with an undefined
        length.
        
        INPUTS:
            reach       = starting reach to calculate upstream length from
            levels      = (optional) see OrderedCollection.trace_up()
            ignoreNone  = (optional) whether to skip (True) when encountering
                reaches with an undefined length. Default is True.
                
        OUTPUTS: float of the total length upstream of the reach
        """
        upstreamReaches = self.trace_up(
            reach, levels, filters={'tributary': self}
        )
        return self.__operate_over__(upstreamReaches, 'length', '+', ignoreNone)
        
        
    def length_down(self, reach, levels=None, ignoreNone=True):
        """
        Calculates the length of the Tributary downstream of the given reach
        within the catchment, optionally ignoring reaches with an undefined 
        length.
        
        INPUTS:
            reach       = starting reach to calculate downstream length from
            levels      = (optional) see OrderedObject.trace_down()
            ignoreNone  = (optional) whether to skip (True) when encountering
                reaches with an undefined length. Default is True.
                
        OUTPUTS: float of the total length downstream of the reach
        """
        downstreamReaches = reach.trace_down(
            levels, filters={'tributary': self}, types=Reach
        )
        return self.__operate_over__(downstreamReaches, 'length', '+', ignoreNone)
        
        
        
# ~~ LAKE ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
class Lake(OrderedCollection):
    
    def __init__(self, tributaries, **attributes):
        
        OrderedCollection.__init__(self, tributaries, **attributes)
        
        # set attributes using defaults and user overrides
        P = {}
        P.update(dict((k.lower(), attributes[k]) for k in attributes))
        for attribute in P:
            setattr(self, attribute, P[attribute])
        self.tributaries = self.objects
        
        # update tributary lake identity
        for tributary in self.tributaries: tributary.lake = self
 
    
    def length_all(self, ignoreNone=True):
        """
        Calculates the total length of tributaries draining into the lake,
        optionally ignoring reaches with undefined lengths.
        """
        return sum([trib.length_all(ignoreNone) for trib in self.tributaries])
        
        
    def area_all(self, ignoreNone=True):
        """
        Calculates the total ara of all catchments draining into self,
        optionally ignoring catchments with undefined area.
        """
        return sum([trib.area_all(ignoreNone) for trib in self.tributaries])
        


        
# ########################################################################### #
# ################################ FUNCTIONS ################################ #
# ########################################################################### #
            
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
            catchments: name of the catchments dataset in the database. Default
                is LOD_DAT_CAT
            tributaries: name of the tributaries dataset in the database.
                Default is LOD_DAT_TRB
            bid_field: unique barrier ID field in barriers dataset. Default is
                LOD_FLD_BID
            bds_field: barrier downstream ID field in barriers dataset. Default
                is LOD_FLD_BDS
            rid_field: flowline ID field in barriers and flowlines dataset. 
                Default is LOD_FLD_RID
            nat_field: country of location of barrier in barriers dataset.
                Default is LOD_FLD_NAT
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
            tid_field: tributary ID field in flowlines and tributaries dataset.
                Default is LOD_FLD_TID
            cat_field: catchment ID field in flowlines and catchments dataset. 
                Default is LOD_FLD_CAT
            cds_field: catchment downstream ID field in catchments dataset.
                Default is LOD_FLD_CDS
            len_field: flowline's length field in flowlines dataset. Default
                is LOD_FLD_LEN
            sto_field: flowline's stream order field in flowlines dataset.
                Default is LOD_FLD_STO
            wsa_field: catchment's area field in catchments dataset. Default
                is LOD_FLD_WSA
            lak_field: lake into which tributary flows in tributaries dataset. 
                Default is LOD_FLD_LAK
            slf_value: value that indicates the downstream barrier, flowline,
                or catchment is itself. Default is LOD_VAL_SLF
                
    OUTPUT: a dictionary formatted for create_hydrography()
    """
    
    # imports
    import arcpy, os
    
    # update options
    P = {
        'barriers': LOD_DAT_BAR, 'flowlines': LOD_DAT_FLO,
        'catchments': LOD_DAT_CAT, 'tributaries': LOD_DAT_TRB, 
        'bid_field': LOD_FLD_BID, 'bds_field': LOD_FLD_BDS,
        'rid_field': LOD_FLD_RID, 'nat_field': LOD_FLD_NAT,
        'fpr_field': LOD_FLD_FPR, 'hab_field': LOD_FLD_HAB,
        'cst_field': LOD_FLD_CST, 'lam_field': LOD_FLD_LAM,
        'low_field': LOD_FLD_P04, 'mid_field': LOD_FLD_P07,
        'hih_field': LOD_FLD_P10, 'rds_field': LOD_FLD_RDS,
        'tid_field': LOD_FLD_TID, 'cat_field': LOD_FLD_CAT,
        'len_field': LOD_FLD_LEN, 'sto_field': LOD_FLD_STO,
        'wsa_field': LOD_FLD_WSA, 'lak_field': LOD_FLD_LAK,
        'cds_field': LOD_FLD_CDS, 'slf_value': LOD_VAL_SLF
        
    }
    for k in options: P[k.lower()] = options[k]
    
    
    # ~~ DEFINE CONSTANTS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    
    # define datasets for loading
    datasets = {
        'barriers': os.path.join(database, P['barriers']),
        'flowlines': os.path.join(database, P['flowlines']),
        'catchments': os.path.join(database, P['catchments']),
        'tributaries': os.path.join(database, P['tributaries'])
    }
    
    # define fields to load for each dataset
    fields = {
        'barriers': (
            'bid_field', 'bds_field', 'rid_field', 'fpr_field', 'hab_field',
            'cst_field', 'nat_field', 'lam_field', 'low_field', 'mid_field',
            'hih_field'
        ),
        'flowlines': (
            'rid_field', 'rds_field', 'tid_field', 'cat_field', 'len_field',
            'sto_field'
        ),
        'catchments': ('cat_field', 'cds_field', 'wsa_field'),
        'tributaries': ('tid_field', 'lak_field')
    }
    
    # define fields for which values should be mapped to other values
    val2Val = {
        'barriers': {'bds_field': (P['slf_value'], None)},
        'flowlines': {'rds_field': (P['slf_value'], None)},
        'catchments': {'cds_field': (P['slf_value'], None)}
    }
    
    # mapping from this dataset's fields to the formatted fields for 
    #   create_hydrography()
    fmap = {
        'barriers': (
            CRH_DAT_BAR, {
                'bid_field': CRH_FLD_BID, 'bds_field': CRH_FLD_BDS,
                'rid_field': CRH_FLD_RID, 'fpr_field': CRH_FLD_FPR,
                'hab_field': CRH_FLD_HAB, 'cst_field': CRH_FLD_CST,
                'nat_field': CRH_FLD_NAT, 'lam_field': CRH_FLD_LAM,
                'low_field': CRH_FLD_P04, 'mid_field': CRH_FLD_P07,
                'hih_field': CRH_FLD_P10
            }
        ),
        'flowlines': (
            CRH_DAT_FLO, {
                'rid_field': CRH_FLD_RID, 'rds_field': CRH_FLD_RDS,
                'tid_field': CRH_FLD_RID, 'cat_field': CRH_FLD_CAT,
                'len_field': CRH_FLD_LEN, 'sto_field': CRH_FLD_STO
            }
        ),
        'catchments': (
            CRH_DAT_CAT, 
            {
                'cat_field': CRH_FLD_CAT, 'cds_field': CRH_FLD_CDS,
                'wsa_field': CRH_FLD_WSA
            }
        ),
        'tributaries': (
            CRH_DAT_TRB, 
            {'tid_field': CRH_FLD_TID, 'lak_field': CRH_FLD_LAK}
        )
    }
        
     
    # ~~ DEFINE SUB-DATA FOR PROCESSING DATA ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    
    # mapping from loaded raw value to formatted value
    def map_value(dataset, field, value):
        if (dataset in val2Val) and (field in val2Val[dataset]) and (value == val2Val[dataset][field][0]):
            return val2Val[dataset][field][1]
        else:
            return value
            
    # track index number in data for each field in the loaded data to
    #   make it easy to refer to data in processing in later steps
    fInd = {}
    for k in fields:
        fInd[k] = dict((fmap[k][1][fields[k][i]], i) for i in xrange(len(fields[k])))
            
    # load data
    data = {}
    for datasetName in datasets:
        datasetPath = datasets[datasetName]
        datasetFields = [P[f] for f in fields[datasetName]]
        cursor = arcpy.da.SearchCursor(datasetPath, datasetFields)
        n = len(fields[datasetName])
        
        # load all rows at once, mapping values to new values where need-be
        #   and otherwise just taking the value as is
        try:
            data[fmap[datasetName][0]] = (
                fInd[datasetName],
                [
                    [
                        map_value(
                            datasetName, fields[datasetName][i], row[i]
                        ) for i in xrange(n)
                    ] for row in cursor
                ]
            )
        except Exception as e:
            print str(e)
            import pdb; pdb.set_trace()
            raise
            
        del cursor
        
    return data
        
    
            
# ~~ create_hydrography() ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def create_hydrography(data):
    """
    Creates a Hydrography object from formatted data.
    
    INPUTS:
        data    = formatted hydrography data as returned by load_data()
        
    OUTPUTS: Hydrography object with hydrography sub-objects in the network.
    """
    pass
    
    

def __test__():

    # Test Data
    
    # Barriers
    BA = Barrier(id='BA', country='USA', fprop=0.1, passabilities={'04':1.0, '03':0.4})
    BB = Barrier(id='BB', country='USA', fprop=0.2, passabilities={'04':1.0, '03':0.4})
    BC = Barrier(id='BC', country='USA', fprop=0.3, passabilities={'04':1.0, '03':0.4})
    BD = Barrier(id='BD', country='USA', fprop=0.1, passabilities={'04':1.0, '03':0.4})
    BE = Barrier(id='BE', country='USA', fprop=0.2, passabilities={'04':1.0, '03':0.4})
    BF = Barrier(id='BF', country='USA', fprop=0.3, passabilities={'04':1.0, '03':0.4})
    BG = Barrier(id='BG', country='USA', fprop=0.4, passabilities={'04':1.0, '03':0.4})
    BH = Barrier(id='BH', country='USA', fprop=0.1, passabilities={'04':1.0, '03':0.4})
    BI = Barrier(id='BI', country='USA', fprop=0.2, passabilities={'04':1.0, '03':0.4})
    BJ = Barrier(id='BJ', country='USA', fprop=0.3, passabilities={'04':1.0, '03':0.4})
    BK = Barrier(id='BK', country='USA', fprop=0.1, passabilities={'04':1.0, '03':0.4})
    BL = Barrier(id='BL', country='USA', fprop=0.2, passabilities={'04':1.0, '03':0.4})
    BM = Barrier(id='BM', country='USA', fprop=0.1, passabilities={'04':1.0, '03':0.4})
    BN = Barrier(id='BN', country='USA', fprop=0.1, passabilities={'04':1.0, '03':0.4})
    BA.down = BB
    BB.down = BC
    BC.down = BH
    BD.down = BF
    BE.down = BF
    BF.down = BG
    BG.down = BJ
    BI.down = BJ
    BK.down = BL
    BL.down = BN
    BM.down = BN

    # Reaches
    RA = Reach(id='RA', length=1.1, barriers=set([BA]))
    RB = Reach(id='RB', length=1.2)
    RC = Reach(id='RC', length=1.3, barriers=set([BB, BC]))
    RD = Reach(id='RD', length=1.4)
    RE = Reach(id='RE', length=1.5)
    RF = Reach(id='RF', length=1.1, barriers=set([BD]))
    RG = Reach(id='RG', length=1.2, barriers=set([BE]))
    RH = Reach(id='RH', length=1.3, barriers=set([BF, BG]))
    RI = Reach(id='RI', length=1.1, barriers=set([BH]))
    RJ = Reach(id='RJ', length=1.2, barriers=set([BI]))
    RK = Reach(id='RK', length=1.3)
    RL = Reach(id='RL', length=1.4)
    RM = Reach(id='RM', length=1.5)
    RN = Reach(id='RN', length=1.6, barriers=set([BJ]))
    RO = Reach(id='RO', length=1.7)
    RP = Reach(id='RP', length=1.1, barriers=set([BK, BL]))
    RQ = Reach(id='RQ', length=1.1)
    RR = Reach(id='RR', length=1.2, barriers=set([BM]))
    RS = Reach(id='RS', length=1.3)
    RT = Reach(id='RT', length=1.1, barrieres=set([BN]))
    RU = Reach(id='RU', length=1.2)
    RV = Reach(id='RV', length=1.3)
    RA.down = RC
    RB.down = RC
    RC.down = RE
    RD.down = RE
    RE.down = RI
    RF.down = RH
    RG.down = RH
    RH.down = RK
    RI.down = RO
    RJ.down = RM
    RK.down = RM
    RL.down = RN
    RM.down = RN
    RN.down = RO
    RP.down = RQ
    RQ.down = RS
    RR.down = RS
    RS.down = RT
    RT.down = RV
    RU.down = RV

    # Catchments
    CA = Catchment(id='CA', area=10.1, reaches=set([RA, RB, RC, RD, RE]))
    CB = Catchment(id='CB', area=10.2, reaches=set([RF, RG, RH]))
    CC = Catchment(id='CC', area=10.1, reaches=set([RP]))
    CD = Catchment(id='CD', area=10.3, reaches=set([RI, RJ, RK, RL, RM, RN, RO]))
    CE = Catchment(id='CE', area=10.2, reaches=set([RQ, RR, RS]))
    CF = Catchment(id='CF', area=10.3, reaches=set([RT, RU, RV]))
    CA.down = CD
    CB.down = CD
    CC.down = CE
    CE.down = CF
    
    # Tributaries
    taReaches = CA.reaches.union(CB.reaches).union(CD.reaches)
    TA = Tributary(taReaches)
    tbReaches = CC.reaches.union(CE.reaches).union(CF.reaches)
    TB = Tributary(tbReaches)
    
    LA = Lake([TA, TB])
    
    # Tests
    epsilon = 1e5
    tests = (
        'RA.trace_down() == [RC, RE, RI, RO]', # reach's downstream trace is correct
        'CC.trace_down() == [CE, CF]', # catchment's down-stream trace is correct
        'BE.trace_down() == [BF, BG, BJ]', # barrier's down-stream trace is correct
        'RS.catchment.trace_up(RS) == set([RR, RQ])', # reach's up-catchment trace is correct
        'abs(CE.length_all() - (RS.length + RR.length + RQ.length)) < epsilon', # catchment's length_all is correct
        'abs(RO.catchment.length_up(RO, levels=2) - (RN.length + RM.length + RL.length + RI.length)) < epsilon', # catchment's length-up is correct
        'RG.catchment.length_down(RG) == RH.length', # catchment's length_down is correct
        'RM.tributary.trace_up(RM) == set([RG, RJ, RF, RK, RH])', # reach's up-tributary-trace is correct
        'CF.tributary.trace_up(CF) == set([CC, CE])', # catchment's up-tributary trace is correct
        'BJ.tributary.trace_up(BJ) == set([BI, BF, BD, BG, BE])', # barrier's up-tributary trace is correct
        'abs(CD.tributary.area_up(CD) - (CA.area + CB.area)) < epsilon', # tributary area_up is correct
        'CB.tributary.area_down(CB) == CD.area', # tributary area_down is correct
        'abs(RP.tributary.length_all() - sum([r.length for r in (RP, RQ, RR, RS, RT, RU, RV)])) < epsilon', # tributary's length_all is correct
        'abs(RM.tributary.length_up(RM) - sum([r.length for r in (RJ, RK, RH, RF, RG)])) < epsilon', # tributary's length_up is correct
        'abs(RM.tributary.length_down(RM) - sum([r.length for r in (RN, RO)])) < epsilon', # tributary's length_down is correct
        'abs(LA.area_all() - (CA.area + CB.area + CC.area + CD.area + CE.area + CF.area)) < epsilon', # sum of areas matches in area_all function
        'abs(LA.length_all() - sum([r.length for r in (RA, RB, RC, RD, RE, RF, RG, RH, RI, RJ, RK, RL, RM, RN, RO, RP, RQ, RR, RS, RT, RU, RV)])) < epsilon', # lake's length_all is correct
        'BJ.reach.trace_up(BJ) == set()', # barriers with no upstream barriers have empty upstream set
        'RL.tributary.length_up(RL) == 0.' # reaches without upstream reaches have up length == 0
    )
    failures = 0
    for test in tests:
        try:
            result = eval(test)
            if result == True: print 'PASSED: %s' % test
            else:
                print 'FAILED: %s' % test
                failures += 1
            
        except Exception as e:
            print 'FAILED with Exception (%s): %s' % (str(e), test)
            failures += 1
            
    if failures > 0:
        import pdb; pdb.set_trace()
            
    
if __name__ == '__main__':
    __test__()
    
    database = r'C:\Users\milt\Dropbox\UW Madison Post Doc\Data(Temp)\Barriers\hydro_update\GL_pruned_hydrography.mdb'
    data = load_data(database)
    
    #     --- data table ---    row     --- fields dict ---  field
    print data['barriers'][1]   [0]  [  data['barriers'][0] ['bid']  ]
    
    ## load the database
    ## pass into create_hydrography
    
