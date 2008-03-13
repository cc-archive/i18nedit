_MSADERR_H_ = ""
#+---------------------------------------------------------------------------
#
#  Microsoft OLE DB
#  Copyright (C) Microsoft Corporation, 1994 - 1998.
#
#----------------------------------------------------------------------------


#
#  Values are 32 bit values layed out as follows:
#
#   3 3 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 1 1
#   1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
#  +-+-+-+-+-+---------------------+-------------------------------+
#  |S|R|C|N|r|    Facility         |               Code            |
#  +-+-+-+-+-+---------------------+-------------------------------+
#
#  where
#
#      S - Severity - indicates success/fail
#
#          0 - Success
#          1 - Fail (COERROR)
#
#      R - reserved portion of the facility code, corresponds to NT's
#              second severity bit.
#
#      C - reserved portion of the facility code, corresponds to NT's
#              C field.
#
#      N - reserved portion of the facility code. Used to indicate a
#              mapped NT status value.
#
#      r - reserved portion of the facility code. Reserved for internal
#              use. Used to indicate HRESULT values that are not status
#              values, but are instead message ids for display strings.
#
#      Facility - is the facility code
#
#      Code - is the facility's status code
#
#
# Define the facility codes
#
FACILITY_WINDOWS = "0x8"
FACILITY_ITF = "0x4"


#
# Define the severity codes
#
STATUS_SEVERITY_SUCCESS = "0x0"
STATUS_SEVERITY_COERROR = "0x2"


#
# MessageId: DB_E_BOGUS
#
# MessageText:
#
#  Dummy error - need this error so that mc puts the above defines
#  inside the FACILITY_WINDOWS guard, instead of leaving it empty
#
DB_E_BOGUS = 0x80040EFFL


#
# Codes 0x0e00-0x0eff are reserved for the OLE DB group of
# interfaces.
#
# Free codes are:
#
#		Error:
#			-none-
#
#		Success:
#			0x0eea
#			0x0ed7
#


#
# OLEDBVER
#	OLE DB version number (0x0200); this can be overridden with an older
# version number if necessary
#

# If OLEDBVER is not defined, assume version 2.0
OLEDBVER = "0x0200"

#
# MessageId: DB_E_BADACCESSORHANDLE
#
# MessageText:
#
#  Invalid accessor
#
DB_E_BADACCESSORHANDLE = 0x80040E00L

#
# MessageId: DB_E_ROWLIMITEXCEEDED
#
# MessageText:
#
#  Creating another row would have exceeded the total number of active
#  rows supported by the rowset
#
DB_E_ROWLIMITEXCEEDED = 0x80040E01L

#
# MessageId: DB_E_READONLYACCESSOR
#
# MessageText:
#
#  Unable to write with a read-only accessor
#
DB_E_READONLYACCESSOR = 0x80040E02L

#
# MessageId: DB_E_SCHEMAVIOLATION
#
# MessageText:
#
#  Given values violate the database schema
#
DB_E_SCHEMAVIOLATION = 0x80040E03L

#
# MessageId: DB_E_BADROWHANDLE
#
# MessageText:
#
#  Invalid row handle
#
DB_E_BADROWHANDLE = 0x80040E04L

#
# MessageId: DB_E_OBJECTOPEN
#
# MessageText:
#
#  An object was open
#
DB_E_OBJECTOPEN = 0x80040E05L

#@@@+ V1.5
#
# MessageId: DB_E_BADCHAPTER
#
# MessageText:
#
#  Invalid chapter
#
DB_E_BADCHAPTER = 0x80040E06L

#@@@- V1.5

#
# MessageId: DB_E_CANTCONVERTVALUE
#
# MessageText:
#
#  A literal value in the command could not be converted to the
#  correct type due to a reason other than data overflow
#
DB_E_CANTCONVERTVALUE = 0x80040E07L

#
# MessageId: DB_E_BADBINDINFO
#
# MessageText:
#
#  Invalid binding info
#
DB_E_BADBINDINFO = 0x80040E08L

#
# MessageId: DB_SEC_E_PERMISSIONDENIED
#
# MessageText:
#
#  Permission denied
#
DB_SEC_E_PERMISSIONDENIED = 0x80040E09L

#
# MessageId: DB_E_NOTAREFERENCECOLUMN
#
# MessageText:
#
#  Specified column does not contain bookmarks or chapters
#
DB_E_NOTAREFERENCECOLUMN = 0x80040E0AL

#@@@+ V2.5
#
# MessageId: DB_E_LIMITREJECTED
#
# MessageText:
#
#  Some cost limits were rejected
#
DB_E_LIMITREJECTED = 0x80040E0BL

#@@@- V2.5

#
# MessageId: DB_E_NOCOMMAND
#
# MessageText:
#
#  No command has been set for the command object
#
DB_E_NOCOMMAND = 0x80040E0CL

#@@@+ V2.5
#
# MessageId: DB_E_COSTLIMIT
#
# MessageText:
#
#  Unable to find a query plan within the given cost limit
#
DB_E_COSTLIMIT = 0x80040E0DL

#@@@- V2.5

#
# MessageId: DB_E_BADBOOKMARK
#
# MessageText:
#
#  Invalid bookmark
#
DB_E_BADBOOKMARK = 0x80040E0EL

#
# MessageId: DB_E_BADLOCKMODE
#
# MessageText:
#
#  Invalid lock mode
#
DB_E_BADLOCKMODE = 0x80040E0FL

#
# MessageId: DB_E_PARAMNOTOPTIONAL
#
# MessageText:
#
#  No value given for one or more required parameters
#
DB_E_PARAMNOTOPTIONAL = 0x80040E10L

#
# MessageId: DB_E_BADCOLUMNID
#
# MessageText:
#
#  Invalid column ID
#
DB_E_BADCOLUMNID = 0x80040E11L

#
# MessageId: DB_E_BADRATIO
#
# MessageText:
#
#  Invalid ratio
#
DB_E_BADRATIO = 0x80040E12L

#@@@+ V2.0
#
# MessageId: DB_E_BADVALUES
#
# MessageText:
#
#  Invalid value
#
DB_E_BADVALUES = 0x80040E13L

#@@@- V2.0

#
# MessageId: DB_E_ERRORSINCOMMAND
#
# MessageText:
#
#  The command contained one or more errors
#
DB_E_ERRORSINCOMMAND = 0x80040E14L

#
# MessageId: DB_E_CANTCANCEL
#
# MessageText:
#
#  The executing command cannot be canceled
#
DB_E_CANTCANCEL = 0x80040E15L

#
# MessageId: DB_E_DIALECTNOTSUPPORTED
#
# MessageText:
#
#  The provider does not support the specified dialect
#
DB_E_DIALECTNOTSUPPORTED = 0x80040E16L

#
# MessageId: DB_E_DUPLICATEDATASOURCE
#
# MessageText:
#
#  A data source with the specified name already exists
#
DB_E_DUPLICATEDATASOURCE = 0x80040E17L

#
# MessageId: DB_E_CANNOTRESTART
#
# MessageText:
#
#  The rowset was built over a live data feed and cannot be restarted
#
DB_E_CANNOTRESTART = 0x80040E18L

#
# MessageId: DB_E_NOTFOUND
#
# MessageText:
#
#  No key matching the described characteristics could be found within
#  the current range
#
DB_E_NOTFOUND = 0x80040E19L

#
# MessageId: DB_E_NEWLYINSERTED
#
# MessageText:
#
#  The provider is unable to determine identity for newly inserted
#  rows
#
DB_E_NEWLYINSERTED = 0x80040E1BL

#@@@+ V2.5
#
# MessageId: DB_E_CANNOTFREE
#
# MessageText:
#
#  Ownership of this tree has been given to the provider
#
DB_E_CANNOTFREE = 0x80040E1AL

#
# MessageId: DB_E_GOALREJECTED
#
# MessageText:
#
#  No nonzero weights specified for any goals supported, so goal was
#  rejected; current goal was not changed
#
DB_E_GOALREJECTED = 0x80040E1CL

#@@@- V2.5

#
# MessageId: DB_E_UNSUPPORTEDCONVERSION
#
# MessageText:
#
#  Requested conversion is not supported
#
DB_E_UNSUPPORTEDCONVERSION = 0x80040E1DL

#
# MessageId: DB_E_BADSTARTPOSITION
#
# MessageText:
#
#  lRowsOffset would position you past either end of the rowset,
#  regardless of the cRows value specified; cRowsObtained is 0
#
DB_E_BADSTARTPOSITION = 0x80040E1EL

#@@@+ V2.0
#
# MessageId: DB_E_NOQUERY
#
# MessageText:
#
#  Information was requested for a query, and the query was not set
#
DB_E_NOQUERY = 0x80040E1FL

#@@@- V2.0

#
# MessageId: DB_E_NOTREENTRANT
#
# MessageText:
#
#  Provider called a method from IRowsetNotify in the consumer and	the
#  method has not yet returned
#
DB_E_NOTREENTRANT = 0x80040E20L

#
# MessageId: DB_E_ERRORSOCCURRED
#
# MessageText:
#
#  Errors occurred
#
DB_E_ERRORSOCCURRED = 0x80040E21L

#
# MessageId: DB_E_NOAGGREGATION
#
# MessageText:
#
#  A non-NULL controlling IUnknown was specified and the object being
#  created does not support aggregation
#
DB_E_NOAGGREGATION = 0x80040E22L

#
# MessageId: DB_E_DELETEDROW
#
# MessageText:
#
#  A given HROW referred to a hard- or soft-deleted row
#
DB_E_DELETEDROW = 0x80040E23L

#
# MessageId: DB_E_CANTFETCHBACKWARDS
#
# MessageText:
#
#  The rowset does not support fetching backwards
#
DB_E_CANTFETCHBACKWARDS = 0x80040E24L

#
# MessageId: DB_E_ROWSNOTRELEASED
#
# MessageText:
#
#  All HROWs must be released before new ones can be obtained
#
DB_E_ROWSNOTRELEASED = 0x80040E25L

#
# MessageId: DB_E_BADSTORAGEFLAG
#
# MessageText:
#
#  One of the specified storage flags was not supported
#
DB_E_BADSTORAGEFLAG = 0x80040E26L

#@@@+ V1.5
#
# MessageId: DB_E_BADCOMPAREOP
#
# MessageText:
#
#  The comparison operator was invalid
#
DB_E_BADCOMPAREOP = 0x80040E27L

#@@@- V1.5

#
# MessageId: DB_E_BADSTATUSVALUE
#
# MessageText:
#
#  The specified status flag was neither DBCOLUMNSTATUS_OK nor
#  DBCOLUMNSTATUS_ISNULL
#
DB_E_BADSTATUSVALUE = 0x80040E28L

#
# MessageId: DB_E_CANTSCROLLBACKWARDS
#
# MessageText:
#
#  The rowset cannot scroll backwards
#
DB_E_CANTSCROLLBACKWARDS = 0x80040E29L

#@@@+ V2.5
#
# MessageId: DB_E_BADREGIONHANDLE
#
# MessageText:
#
#  Invalid region handle
#
DB_E_BADREGIONHANDLE = 0x80040E2AL

#
# MessageId: DB_E_NONCONTIGUOUSRANGE
#
# MessageText:
#
#  The specified set of rows was not contiguous to or overlapping the
#  rows in the specified watch region
#
DB_E_NONCONTIGUOUSRANGE = 0x80040E2BL

#
# MessageId: DB_E_INVALIDTRANSITION
#
# MessageText:
#
#  A transition from ALL* to MOVE* or EXTEND* was specified
#
DB_E_INVALIDTRANSITION = 0x80040E2CL

#
# MessageId: DB_E_NOTASUBREGION
#
# MessageText:
#
#  The specified region is not a proper subregion of the region
#  identified by the given watch region handle
#
DB_E_NOTASUBREGION = 0x80040E2DL

#@@@- V2.5

#
# MessageId: DB_E_MULTIPLESTATEMENTS
#
# MessageText:
#
#  The provider does not support multi-statement commands
#
DB_E_MULTIPLESTATEMENTS = 0x80040E2EL

#
# MessageId: DB_E_INTEGRITYVIOLATION
#
# MessageText:
#
#  A specified value violated the integrity constraints for a column or
#  table
#
DB_E_INTEGRITYVIOLATION = 0x80040E2FL

#
# MessageId: DB_E_BADTYPENAME
#
# MessageText:
#
#  The given type name was unrecognized
#
DB_E_BADTYPENAME = 0x80040E30L

#
# MessageId: DB_E_ABORTLIMITREACHED
#
# MessageText:
#
#  Execution aborted because a resource limit has been reached; no
#  results have been returned
#
DB_E_ABORTLIMITREACHED = 0x80040E31L

#@@@+ V2.0
#
# MessageId: DB_E_ROWSETINCOMMAND
#
# MessageText:
#
#  Cannot clone a command object whose command tree contains a rowset
#  or rowsets
#
DB_E_ROWSETINCOMMAND = 0x80040E32L

#
# MessageId: DB_E_CANTTRANSLATE
#
# MessageText:
#
#  Cannot represent the current tree as text
#
DB_E_CANTTRANSLATE = 0x80040E33L

#@@@- V2.0

#
# MessageId: DB_E_DUPLICATEINDEXID
#
# MessageText:
#
#  The specified index already exists
#
DB_E_DUPLICATEINDEXID = 0x80040E34L

#
# MessageId: DB_E_NOINDEX
#
# MessageText:
#
#  The specified index does not exist
#
DB_E_NOINDEX = 0x80040E35L

#
# MessageId: DB_E_INDEXINUSE
#
# MessageText:
#
#  The specified index was in use
#
DB_E_INDEXINUSE = 0x80040E36L

#
# MessageId: DB_E_NOTABLE
#
# MessageText:
#
#  The specified table does not exist
#
DB_E_NOTABLE = 0x80040E37L

#
# MessageId: DB_E_CONCURRENCYVIOLATION
#
# MessageText:
#
#  The rowset was using optimistic concurrency and the value of a
#  column has been changed since it was last read
#
DB_E_CONCURRENCYVIOLATION = 0x80040E38L

#
# MessageId: DB_E_BADCOPY
#
# MessageText:
#
#  Errors were detected during the copy
#
DB_E_BADCOPY = 0x80040E39L

#
# MessageId: DB_E_BADPRECISION
#
# MessageText:
#
#  A specified precision was invalid
#
DB_E_BADPRECISION = 0x80040E3AL

#
# MessageId: DB_E_BADSCALE
#
# MessageText:
#
#  A specified scale was invalid
#
DB_E_BADSCALE = 0x80040E3BL

#
# MessageId: DB_E_BADTABLEID
#
# MessageText:
#
#  Invalid table ID
#
DB_E_BADTABLEID = 0x80040E3CL

# DB_E_BADID is deprecated; use DB_E_BADTABLEID instead
DB_E_BADID = "DB_E_BADTABLEID"

#
# MessageId: DB_E_BADTYPE
#
# MessageText:
#
#  A specified type was invalid
#
DB_E_BADTYPE = 0x80040E3DL

#
# MessageId: DB_E_DUPLICATECOLUMNID
#
# MessageText:
#
#  A column ID was occurred more than once in the specification
#
DB_E_DUPLICATECOLUMNID = 0x80040E3EL

#
# MessageId: DB_E_DUPLICATETABLEID
#
# MessageText:
#
#  The specified table already exists
#
DB_E_DUPLICATETABLEID = 0x80040E3FL

#
# MessageId: DB_E_TABLEINUSE
#
# MessageText:
#
#  The specified table was in use
#
DB_E_TABLEINUSE = 0x80040E40L

#
# MessageId: DB_E_NOLOCALE
#
# MessageText:
#
#  The specified locale ID was not supported
#
DB_E_NOLOCALE = 0x80040E41L

#
# MessageId: DB_E_BADRECORDNUM
#
# MessageText:
#
#  The specified record number is invalid
#
DB_E_BADRECORDNUM = 0x80040E42L

#
# MessageId: DB_E_BOOKMARKSKIPPED
#
# MessageText:
#
#  Although the bookmark was validly formed, no row could be found to
#  match it
#
DB_E_BOOKMARKSKIPPED = 0x80040E43L

#
# MessageId: DB_E_BADPROPERTYVALUE
#
# MessageText:
#
#  The value of a property was invalid
#
DB_E_BADPROPERTYVALUE = 0x80040E44L

#
# MessageId: DB_E_INVALID
#
# MessageText:
#
#  The rowset was not chaptered
#
DB_E_INVALID = 0x80040E45L

#
# MessageId: DB_E_BADACCESSORFLAGS
#
# MessageText:
#
#  Invalid accessor
#
DB_E_BADACCESSORFLAGS = 0x80040E46L

#
# MessageId: DB_E_BADSTORAGEFLAGS
#
# MessageText:
#
#  Invalid storage flags
#
DB_E_BADSTORAGEFLAGS = 0x80040E47L

#
# MessageId: DB_E_BYREFACCESSORNOTSUPPORTED
#
# MessageText:
#
#  By-ref accessors are not supported by this provider
#
DB_E_BYREFACCESSORNOTSUPPORTED = 0x80040E48L

#
# MessageId: DB_E_NULLACCESSORNOTSUPPORTED
#
# MessageText:
#
#  Null accessors are not supported by this provider
#
DB_E_NULLACCESSORNOTSUPPORTED = 0x80040E49L

#
# MessageId: DB_E_NOTPREPARED
#
# MessageText:
#
#  The command was not prepared
#
DB_E_NOTPREPARED = 0x80040E4AL

#
# MessageId: DB_E_BADACCESSORTYPE
#
# MessageText:
#
#  The specified accessor was not a parameter accessor
#
DB_E_BADACCESSORTYPE = 0x80040E4BL

#
# MessageId: DB_E_WRITEONLYACCESSOR
#
# MessageText:
#
#  The given accessor was write-only
#
DB_E_WRITEONLYACCESSOR = 0x80040E4CL

#
# MessageId: DB_SEC_E_AUTH_FAILED
#
# MessageText:
#
#  Authentication failed
#
DB_SEC_E_AUTH_FAILED = 0x80040E4DL

#
# MessageId: DB_E_CANCELED
#
# MessageText:
#
#  The change was canceled during notification; no columns are changed
#
DB_E_CANCELED = 0x80040E4EL

#@@@+ V2.0
#
# MessageId: DB_E_CHAPTERNOTRELEASED
#
# MessageText:
#
#  The rowset was single-chaptered and the chapter was not released
#
DB_E_CHAPTERNOTRELEASED = 0x80040E4FL

#@@@- V2.0

#
# MessageId: DB_E_BADSOURCEHANDLE
#
# MessageText:
#
#  Invalid source handle
#
DB_E_BADSOURCEHANDLE = 0x80040E50L

#
# MessageId: DB_E_PARAMUNAVAILABLE
#
# MessageText:
#
#  The provider cannot derive parameter info and SetParameterInfo has
#  not been called
#
DB_E_PARAMUNAVAILABLE = 0x80040E51L

#
# MessageId: DB_E_ALREADYINITIALIZED
#
# MessageText:
#
#  The data source object is already initialized
#
DB_E_ALREADYINITIALIZED = 0x80040E52L

#
# MessageId: DB_E_NOTSUPPORTED
#
# MessageText:
#
#  The provider does not support this method
#
DB_E_NOTSUPPORTED = 0x80040E53L

#
# MessageId: DB_E_MAXPENDCHANGESEXCEEDED
#
# MessageText:
#
#  The number of rows with pending changes has exceeded the set limit
#
DB_E_MAXPENDCHANGESEXCEEDED = 0x80040E54L

#
# MessageId: DB_E_BADORDINAL
#
# MessageText:
#
#  The specified column did not exist
#
DB_E_BADORDINAL = 0x80040E55L

#
# MessageId: DB_E_PENDINGCHANGES
#
# MessageText:
#
#  There are pending changes on a row with a reference count of zero
#
DB_E_PENDINGCHANGES = 0x80040E56L

#
# MessageId: DB_E_DATAOVERFLOW
#
# MessageText:
#
#  A literal value in the command overflowed the range of the type of
#  the associated column
#
DB_E_DATAOVERFLOW = 0x80040E57L

#
# MessageId: DB_E_BADHRESULT
#
# MessageText:
#
#  The supplied HRESULT was invalid
#
DB_E_BADHRESULT = 0x80040E58L

#
# MessageId: DB_E_BADLOOKUPID
#
# MessageText:
#
#  The supplied LookupID was invalid
#
DB_E_BADLOOKUPID = 0x80040E59L

#
# MessageId: DB_E_BADDYNAMICERRORID
#
# MessageText:
#
#  The supplied DynamicErrorID was invalid
#
DB_E_BADDYNAMICERRORID = 0x80040E5AL

#
# MessageId: DB_E_PENDINGINSERT
#
# MessageText:
#
#  Unable to get visible data for a newly-inserted row that has not
#  yet been updated
#
DB_E_PENDINGINSERT = 0x80040E5BL

#
# MessageId: DB_E_BADCONVERTFLAG
#
# MessageText:
#
#  Invalid conversion flag
#
DB_E_BADCONVERTFLAG = 0x80040E5CL

#
# MessageId: DB_E_BADPARAMETERNAME
#
# MessageText:
#
#  The given parameter name was unrecognized
#
DB_E_BADPARAMETERNAME = 0x80040E5DL

#
# MessageId: DB_E_MULTIPLESTORAGE
#
# MessageText:
#
#  Multiple storage objects can not be open simultaneously
#
DB_E_MULTIPLESTORAGE = 0x80040E5EL

#
# MessageId: DB_E_CANTFILTER
#
# MessageText:
#
#  The requested filter could not be opened
#
DB_E_CANTFILTER = 0x80040E5FL

#
# MessageId: DB_E_CANTORDER
#
# MessageText:
#
#  The requested order could not be opened
#
DB_E_CANTORDER = 0x80040E60L

#@@@+ V2.0
#
# MessageId: MD_E_BADTUPLE
#
# MessageText:
#
#  Bad tuple
#
MD_E_BADTUPLE = 0x80040E61L

#
# MessageId: MD_E_BADCOORDINATE
#
# MessageText:
#
#  Bad coordinate
#
MD_E_BADCOORDINATE = 0x80040E62L

#
# MessageId: MD_E_INVALIDAXIS
#
# MessageText:
#
#  The given aixs was not valid for this Dataset
#
MD_E_INVALIDAXIS = 0x80040E63L

#
# MessageId: MD_E_INVALIDCELLRANGE
#
# MessageText:
#
#  One or more of the given cell ordinals was invalid
#
MD_E_INVALIDCELLRANGE = 0x80040E64L

#
# MessageId: DB_E_NOCOLUMN
#
# MessageText:
#
#  The supplied columnID was invalid
#
DB_E_NOCOLUMN = 0x80040E65L

#
# MessageId: DB_E_COMMANDNOTPERSISTED
#
# MessageText:
#
#  The supplied command does not have a DBID
#
DB_E_COMMANDNOTPERSISTED = 0x80040E67L

#
# MessageId: DB_E_DUPLICATEID
#
# MessageText:
#
#  The supplied DBID already exists
#
DB_E_DUPLICATEID = 0x80040E68L

#
# MessageId: DB_E_OBJECTCREATIONLIMITREACHED
#
# MessageText:
#
#  The maximum number of Sessions supported by the provider has 
#  already been created. The consumer must release one or more 
#  currently held Sessions before obtaining a new Session Object
#
DB_E_OBJECTCREATIONLIMITREACHED = 0x80040E69L

#
# MessageId: DB_E_BADINDEXID
#
# MessageText:
#
#  The index ID is invalid
#
DB_E_BADINDEXID = 0x80040E72L

#
# MessageId: DB_E_BADINITSTRING
#
# MessageText:
#
#  The initialization string specified does not conform to specificiation
#
DB_E_BADINITSTRING = 0x80040E73L

#
# MessageId: DB_E_NOPROVIDERSREGISTERED
#
# MessageText:
#
#  The OLE DB root enumerator did not return any providers that 
#  matched any of the SOURCES_TYPEs requested
#
DB_E_NOPROVIDERSREGISTERED = 0x80040E74L

#
# MessageId: DB_E_MISMATCHEDPROVIDER
#
# MessageText:
#
#  The initialization string specifies a provider which does not match the currently active provider
#
DB_E_MISMATCHEDPROVIDER = 0x80040E75L

#@@@- V2.0
#@@@+ V2.1
SEC_E_PERMISSIONDENIED = "DB_SEC_E_PERMISSIONDENIED"
#
# MessageId: SEC_E_BADTRUSTEEID
#
# MessageText:
#
#  Invalid trustee value
#
SEC_E_BADTRUSTEEID = 0x80040E6AL

#
# MessageId: SEC_E_NOTRUSTEEID
#
# MessageText:
#
#  The trustee is not for the current data source
#
SEC_E_NOTRUSTEEID = 0x80040E6BL

#
# MessageId: SEC_E_NOMEMBERSHIPSUPPORT
#
# MessageText:
#
#  The trustee does not support memberships/collections
#
SEC_E_NOMEMBERSHIPSUPPORT = 0x80040E6CL

#
# MessageId: SEC_E_INVALIDOBJECT
#
# MessageText:
#
#  The object is invalid or unknown to the provider
#
SEC_E_INVALIDOBJECT = 0x80040E6DL

#
# MessageId: SEC_E_NOOWNER
#
# MessageText:
#
#  No owner exists for the object
#
SEC_E_NOOWNER = 0x80040E6EL

#
# MessageId: SEC_E_INVALIDACCESSENTRYLIST
#
# MessageText:
#
#  The access entry list supplied is invalid
#
SEC_E_INVALIDACCESSENTRYLIST = 0x80040E6FL

#
# MessageId: SEC_E_INVALIDOWNER
#
# MessageText:
#
#  The trustee supplied as owner is invalid or unknown to the provider
#
SEC_E_INVALIDOWNER = 0x80040E70L

#
# MessageId: SEC_E_INVALIDACCESSENTRY
#
# MessageText:
#
#  The permission supplied in the access entry list is invalid
#
SEC_E_INVALIDACCESSENTRY = 0x80040E71L

SEC_E_PERMISSIONDENIED = "DB_SEC_E_PERMISSIONDENIED"
#@@@- V2.1

#
# MessageId: DB_S_ROWLIMITEXCEEDED
#
# MessageText:
#
#  Fetching requested number of rows would have exceeded total number
#  of active rows supported by the rowset
#
DB_S_ROWLIMITEXCEEDED = 0x00040EC0L

#
# MessageId: DB_S_COLUMNTYPEMISMATCH
#
# MessageText:
#
#  One or more column types are incompatible; conversion errors will
#  occur during copying
#
DB_S_COLUMNTYPEMISMATCH = 0x00040EC1L

#
# MessageId: DB_S_TYPEINFOOVERRIDDEN
#
# MessageText:
#
#  Parameter type information has been overridden by caller
#
DB_S_TYPEINFOOVERRIDDEN = 0x00040EC2L

#
# MessageId: DB_S_BOOKMARKSKIPPED
#
# MessageText:
#
#  Skipped bookmark for deleted or non-member row
#
DB_S_BOOKMARKSKIPPED = 0x00040EC3L

#@@@+ V2.0
#
# MessageId: DB_S_NONEXTROWSET
#
# MessageText:
#
#  There are no more rowsets
#
DB_S_NONEXTROWSET = 0x00040EC5L

#@@@- V2.0

#
# MessageId: DB_S_ENDOFROWSET
#
# MessageText:
#
#  Reached start or end of rowset or chapter
#
DB_S_ENDOFROWSET = 0x00040EC6L

#
# MessageId: DB_S_COMMANDREEXECUTED
#
# MessageText:
#
#  The provider re-executed the command
#
DB_S_COMMANDREEXECUTED = 0x00040EC7L

#
# MessageId: DB_S_BUFFERFULL
#
# MessageText:
#
#  Variable data buffer full
#
DB_S_BUFFERFULL = 0x00040EC8L

#
# MessageId: DB_S_NORESULT
#
# MessageText:
#
#  There are no more results
#
DB_S_NORESULT = 0x00040EC9L

#
# MessageId: DB_S_CANTRELEASE
#
# MessageText:
#
#  Server cannot release or downgrade a lock until the end of the
#  transaction
#
DB_S_CANTRELEASE = 0x00040ECAL

#@@@+ V2.5
#
# MessageId: DB_S_GOALCHANGED
#
# MessageText:
#
#  Specified weight was not supported or exceeded the supported limit
#  and was set to 0 or the supported limit
#
DB_S_GOALCHANGED = 0x00040ECBL

#@@@- V2.5

#@@@+ V1.5
#
# MessageId: DB_S_UNWANTEDOPERATION
#
# MessageText:
#
#  Consumer is uninterested in receiving further notification calls for
#  this reason
#
DB_S_UNWANTEDOPERATION = 0x00040ECCL

#@@@- V1.5

#
# MessageId: DB_S_DIALECTIGNORED
#
# MessageText:
#
#  Input dialect was ignored and text was returned in different
#  dialect
#
DB_S_DIALECTIGNORED = 0x00040ECDL

#
# MessageId: DB_S_UNWANTEDPHASE
#
# MessageText:
#
#  Consumer is uninterested in receiving further notification calls for
#  this phase
#
DB_S_UNWANTEDPHASE = 0x00040ECEL

#
# MessageId: DB_S_UNWANTEDREASON
#
# MessageText:
#
#  Consumer is uninterested in receiving further notification calls for
#  this reason
#
DB_S_UNWANTEDREASON = 0x00040ECFL

#@@@+ V1.5
#
# MessageId: DB_S_ASYNCHRONOUS
#
# MessageText:
#
#  The operation is being processed asynchronously
#
DB_S_ASYNCHRONOUS = 0x00040ED0L

#@@@- V1.5

#
# MessageId: DB_S_COLUMNSCHANGED
#
# MessageText:
#
#  In order to reposition to the start of the rowset, the provider had
#  to reexecute the query; either the order of the columns changed or
#  columns were added to or removed from the rowset
#
DB_S_COLUMNSCHANGED = 0x00040ED1L

#
# MessageId: DB_S_ERRORSRETURNED
#
# MessageText:
#
#  The method had some errors; errors have been returned in the error
#  array
#
DB_S_ERRORSRETURNED = 0x00040ED2L

#
# MessageId: DB_S_BADROWHANDLE
#
# MessageText:
#
#  Invalid row handle
#
DB_S_BADROWHANDLE = 0x00040ED3L

#
# MessageId: DB_S_DELETEDROW
#
# MessageText:
#
#  A given HROW referred to a hard-deleted row
#
DB_S_DELETEDROW = 0x00040ED4L

#@@@+ V2.5
#
# MessageId: DB_S_TOOMANYCHANGES
#
# MessageText:
#
#  The provider was unable to keep track of all the changes; the client
#  must refetch the data associated with the watch region using another
#  method
#
DB_S_TOOMANYCHANGES = 0x00040ED5L

#@@@- V2.5

#
# MessageId: DB_S_STOPLIMITREACHED
#
# MessageText:
#
#  Execution stopped because a resource limit has been reached; results
#  obtained so far have been returned but execution cannot be resumed
#
DB_S_STOPLIMITREACHED = 0x00040ED6L

#
# MessageId: DB_S_LOCKUPGRADED
#
# MessageText:
#
#  A lock was upgraded from the value specified
#
DB_S_LOCKUPGRADED = 0x00040ED8L

#
# MessageId: DB_S_PROPERTIESCHANGED
#
# MessageText:
#
#  One or more properties were changed as allowed by provider
#
DB_S_PROPERTIESCHANGED = 0x00040ED9L

#
# MessageId: DB_S_ERRORSOCCURRED
#
# MessageText:
#
#  Errors occurred
#
DB_S_ERRORSOCCURRED = 0x00040EDAL

#
# MessageId: DB_S_PARAMUNAVAILABLE
#
# MessageText:
#
#  A specified parameter was invalid
#
DB_S_PARAMUNAVAILABLE = 0x00040EDBL

#
# MessageId: DB_S_MULTIPLECHANGES
#
# MessageText:
#
#  Updating this row caused more than one row to be updated in the
#  data source
#
DB_S_MULTIPLECHANGES = 0x00040EDCL



errors = {
  DB_E_BOGUS: 'DB_E_BOGUS:\n\n MessageId: DB_E_BOGUS\n\n MessageText:\n\n  Dummy error - need this error so that mc puts the above defines\n  inside the FACILITY_WINDOWS guard, instead of leaving it empty\n',
  DB_E_BADACCESSORHANDLE: 'DB_E_BADACCESSORHANDLE:\n\n MessageId: DB_E_BADACCESSORHANDLE\n\n MessageText:\n\n  Invalid accessor\n',
  DB_E_ROWLIMITEXCEEDED: 'DB_E_ROWLIMITEXCEEDED:\n\n MessageId: DB_E_ROWLIMITEXCEEDED\n\n MessageText:\n\n  Creating another row would have exceeded the total number of active\n  rows supported by the rowset\n',
  DB_E_READONLYACCESSOR: 'DB_E_READONLYACCESSOR:\n\n MessageId: DB_E_READONLYACCESSOR\n\n MessageText:\n\n  Unable to write with a read-only accessor\n',
  DB_E_SCHEMAVIOLATION: 'DB_E_SCHEMAVIOLATION:\n\n MessageId: DB_E_SCHEMAVIOLATION\n\n MessageText:\n\n  Given values violate the database schema\n',
  DB_E_BADROWHANDLE: 'DB_E_BADROWHANDLE:\n\n MessageId: DB_E_BADROWHANDLE\n\n MessageText:\n\n  Invalid row handle\n',
  DB_E_OBJECTOPEN: 'DB_E_OBJECTOPEN:\n\n MessageId: DB_E_OBJECTOPEN\n\n MessageText:\n\n  An object was open\n',
  DB_E_BADCHAPTER: 'DB_E_BADCHAPTER:\n@@@+ V1.5\n\n MessageId: DB_E_BADCHAPTER\n\n MessageText:\n\n  Invalid chapter\n',
  DB_E_CANTCONVERTVALUE: 'DB_E_CANTCONVERTVALUE:\n\n MessageId: DB_E_CANTCONVERTVALUE\n\n MessageText:\n\n  A literal value in the command could not be converted to the\n  correct type due to a reason other than data overflow\n',
  DB_E_BADBINDINFO: 'DB_E_BADBINDINFO:\n\n MessageId: DB_E_BADBINDINFO\n\n MessageText:\n\n  Invalid binding info\n',
  DB_SEC_E_PERMISSIONDENIED: 'DB_SEC_E_PERMISSIONDENIED:\n\n MessageId: DB_SEC_E_PERMISSIONDENIED\n\n MessageText:\n\n  Permission denied\n',
  DB_E_NOTAREFERENCECOLUMN: 'DB_E_NOTAREFERENCECOLUMN:\n\n MessageId: DB_E_NOTAREFERENCECOLUMN\n\n MessageText:\n\n  Specified column does not contain bookmarks or chapters\n',
  DB_E_LIMITREJECTED: 'DB_E_LIMITREJECTED:\n@@@+ V2.5\n\n MessageId: DB_E_LIMITREJECTED\n\n MessageText:\n\n  Some cost limits were rejected\n',
  DB_E_NOCOMMAND: 'DB_E_NOCOMMAND:\n\n MessageId: DB_E_NOCOMMAND\n\n MessageText:\n\n  No command has been set for the command object\n',
  DB_E_COSTLIMIT: 'DB_E_COSTLIMIT:\n@@@+ V2.5\n\n MessageId: DB_E_COSTLIMIT\n\n MessageText:\n\n  Unable to find a query plan within the given cost limit\n',
  DB_E_BADBOOKMARK: 'DB_E_BADBOOKMARK:\n\n MessageId: DB_E_BADBOOKMARK\n\n MessageText:\n\n  Invalid bookmark\n',
  DB_E_BADLOCKMODE: 'DB_E_BADLOCKMODE:\n\n MessageId: DB_E_BADLOCKMODE\n\n MessageText:\n\n  Invalid lock mode\n',
  DB_E_PARAMNOTOPTIONAL: 'DB_E_PARAMNOTOPTIONAL:\n\n MessageId: DB_E_PARAMNOTOPTIONAL\n\n MessageText:\n\n  No value given for one or more required parameters\n',
  DB_E_BADCOLUMNID: 'DB_E_BADCOLUMNID:\n\n MessageId: DB_E_BADCOLUMNID\n\n MessageText:\n\n  Invalid column ID\n',
  DB_E_BADRATIO: 'DB_E_BADRATIO:\n\n MessageId: DB_E_BADRATIO\n\n MessageText:\n\n  Invalid ratio\n',
  DB_E_BADVALUES: 'DB_E_BADVALUES:\n@@@+ V2.0\n\n MessageId: DB_E_BADVALUES\n\n MessageText:\n\n  Invalid value\n',
  DB_E_ERRORSINCOMMAND: 'DB_E_ERRORSINCOMMAND:\n\n MessageId: DB_E_ERRORSINCOMMAND\n\n MessageText:\n\n  The command contained one or more errors\n',
  DB_E_CANTCANCEL: 'DB_E_CANTCANCEL:\n\n MessageId: DB_E_CANTCANCEL\n\n MessageText:\n\n  The executing command cannot be canceled\n',
  DB_E_DIALECTNOTSUPPORTED: 'DB_E_DIALECTNOTSUPPORTED:\n\n MessageId: DB_E_DIALECTNOTSUPPORTED\n\n MessageText:\n\n  The provider does not support the specified dialect\n',
  DB_E_DUPLICATEDATASOURCE: 'DB_E_DUPLICATEDATASOURCE:\n\n MessageId: DB_E_DUPLICATEDATASOURCE\n\n MessageText:\n\n  A data source with the specified name already exists\n',
  DB_E_CANNOTRESTART: 'DB_E_CANNOTRESTART:\n\n MessageId: DB_E_CANNOTRESTART\n\n MessageText:\n\n  The rowset was built over a live data feed and cannot be restarted\n',
  DB_E_NOTFOUND: 'DB_E_NOTFOUND:\n\n MessageId: DB_E_NOTFOUND\n\n MessageText:\n\n  No key matching the described characteristics could be found within\n  the current range\n',
  DB_E_NEWLYINSERTED: 'DB_E_NEWLYINSERTED:\n\n MessageId: DB_E_NEWLYINSERTED\n\n MessageText:\n\n  The provider is unable to determine identity for newly inserted\n  rows\n',
  DB_E_CANNOTFREE: 'DB_E_CANNOTFREE:\n@@@+ V2.5\n\n MessageId: DB_E_CANNOTFREE\n\n MessageText:\n\n  Ownership of this tree has been given to the provider\n',
  DB_E_GOALREJECTED: 'DB_E_GOALREJECTED:\n\n MessageId: DB_E_GOALREJECTED\n\n MessageText:\n\n  No nonzero weights specified for any goals supported, so goal was\n  rejected; current goal was not changed\n',
  DB_E_UNSUPPORTEDCONVERSION: 'DB_E_UNSUPPORTEDCONVERSION:\n\n MessageId: DB_E_UNSUPPORTEDCONVERSION\n\n MessageText:\n\n  Requested conversion is not supported\n',
  DB_E_BADSTARTPOSITION: 'DB_E_BADSTARTPOSITION:\n\n MessageId: DB_E_BADSTARTPOSITION\n\n MessageText:\n\n  lRowsOffset would position you past either end of the rowset,\n  regardless of the cRows value specified; cRowsObtained is 0\n',
  DB_E_NOQUERY: 'DB_E_NOQUERY:\n@@@+ V2.0\n\n MessageId: DB_E_NOQUERY\n\n MessageText:\n\n  Information was requested for a query, and the query was not set\n',
  DB_E_NOTREENTRANT: 'DB_E_NOTREENTRANT:\n\n MessageId: DB_E_NOTREENTRANT\n\n MessageText:\n\n  Provider called a method from IRowsetNotify in the consumer and\tthe\n  method has not yet returned\n',
  DB_E_ERRORSOCCURRED: 'DB_E_ERRORSOCCURRED:\n\n MessageId: DB_E_ERRORSOCCURRED\n\n MessageText:\n\n  Errors occurred\n',
  DB_E_NOAGGREGATION: 'DB_E_NOAGGREGATION:\n\n MessageId: DB_E_NOAGGREGATION\n\n MessageText:\n\n  A non-NULL controlling IUnknown was specified and the object being\n  created does not support aggregation\n',
  DB_E_DELETEDROW: 'DB_E_DELETEDROW:\n\n MessageId: DB_E_DELETEDROW\n\n MessageText:\n\n  A given HROW referred to a hard- or soft-deleted row\n',
  DB_E_CANTFETCHBACKWARDS: 'DB_E_CANTFETCHBACKWARDS:\n\n MessageId: DB_E_CANTFETCHBACKWARDS\n\n MessageText:\n\n  The rowset does not support fetching backwards\n',
  DB_E_ROWSNOTRELEASED: 'DB_E_ROWSNOTRELEASED:\n\n MessageId: DB_E_ROWSNOTRELEASED\n\n MessageText:\n\n  All HROWs must be released before new ones can be obtained\n',
  DB_E_BADSTORAGEFLAG: 'DB_E_BADSTORAGEFLAG:\n\n MessageId: DB_E_BADSTORAGEFLAG\n\n MessageText:\n\n  One of the specified storage flags was not supported\n',
  DB_E_BADCOMPAREOP: 'DB_E_BADCOMPAREOP:\n@@@+ V1.5\n\n MessageId: DB_E_BADCOMPAREOP\n\n MessageText:\n\n  The comparison operator was invalid\n',
  DB_E_BADSTATUSVALUE: 'DB_E_BADSTATUSVALUE:\n\n MessageId: DB_E_BADSTATUSVALUE\n\n MessageText:\n\n  The specified status flag was neither DBCOLUMNSTATUS_OK nor\n  DBCOLUMNSTATUS_ISNULL\n',
  DB_E_CANTSCROLLBACKWARDS: 'DB_E_CANTSCROLLBACKWARDS:\n\n MessageId: DB_E_CANTSCROLLBACKWARDS\n\n MessageText:\n\n  The rowset cannot scroll backwards\n',
  DB_E_BADREGIONHANDLE: 'DB_E_BADREGIONHANDLE:\n@@@+ V2.5\n\n MessageId: DB_E_BADREGIONHANDLE\n\n MessageText:\n\n  Invalid region handle\n',
  DB_E_NONCONTIGUOUSRANGE: 'DB_E_NONCONTIGUOUSRANGE:\n\n MessageId: DB_E_NONCONTIGUOUSRANGE\n\n MessageText:\n\n  The specified set of rows was not contiguous to or overlapping the\n  rows in the specified watch region\n',
  DB_E_INVALIDTRANSITION: 'DB_E_INVALIDTRANSITION:\n\n MessageId: DB_E_INVALIDTRANSITION\n\n MessageText:\n\n  A transition from ALL* to MOVE* or EXTEND* was specified\n',
  DB_E_NOTASUBREGION: 'DB_E_NOTASUBREGION:\n\n MessageId: DB_E_NOTASUBREGION\n\n MessageText:\n\n  The specified region is not a proper subregion of the region\n  identified by the given watch region handle\n',
  DB_E_MULTIPLESTATEMENTS: 'DB_E_MULTIPLESTATEMENTS:\n\n MessageId: DB_E_MULTIPLESTATEMENTS\n\n MessageText:\n\n  The provider does not support multi-statement commands\n',
  DB_E_INTEGRITYVIOLATION: 'DB_E_INTEGRITYVIOLATION:\n\n MessageId: DB_E_INTEGRITYVIOLATION\n\n MessageText:\n\n  A specified value violated the integrity constraints for a column or\n  table\n',
  DB_E_BADTYPENAME: 'DB_E_BADTYPENAME:\n\n MessageId: DB_E_BADTYPENAME\n\n MessageText:\n\n  The given type name was unrecognized\n',
  DB_E_ABORTLIMITREACHED: 'DB_E_ABORTLIMITREACHED:\n\n MessageId: DB_E_ABORTLIMITREACHED\n\n MessageText:\n\n  Execution aborted because a resource limit has been reached; no\n  results have been returned\n',
  DB_E_ROWSETINCOMMAND: 'DB_E_ROWSETINCOMMAND:\n@@@+ V2.0\n\n MessageId: DB_E_ROWSETINCOMMAND\n\n MessageText:\n\n  Cannot clone a command object whose command tree contains a rowset\n  or rowsets\n',
  DB_E_CANTTRANSLATE: 'DB_E_CANTTRANSLATE:\n\n MessageId: DB_E_CANTTRANSLATE\n\n MessageText:\n\n  Cannot represent the current tree as text\n',
  DB_E_DUPLICATEINDEXID: 'DB_E_DUPLICATEINDEXID:\n\n MessageId: DB_E_DUPLICATEINDEXID\n\n MessageText:\n\n  The specified index already exists\n',
  DB_E_NOINDEX: 'DB_E_NOINDEX:\n\n MessageId: DB_E_NOINDEX\n\n MessageText:\n\n  The specified index does not exist\n',
  DB_E_INDEXINUSE: 'DB_E_INDEXINUSE:\n\n MessageId: DB_E_INDEXINUSE\n\n MessageText:\n\n  The specified index was in use\n',
  DB_E_NOTABLE: 'DB_E_NOTABLE:\n\n MessageId: DB_E_NOTABLE\n\n MessageText:\n\n  The specified table does not exist\n',
  DB_E_CONCURRENCYVIOLATION: 'DB_E_CONCURRENCYVIOLATION:\n\n MessageId: DB_E_CONCURRENCYVIOLATION\n\n MessageText:\n\n  The rowset was using optimistic concurrency and the value of a\n  column has been changed since it was last read\n',
  DB_E_BADCOPY: 'DB_E_BADCOPY:\n\n MessageId: DB_E_BADCOPY\n\n MessageText:\n\n  Errors were detected during the copy\n',
  DB_E_BADPRECISION: 'DB_E_BADPRECISION:\n\n MessageId: DB_E_BADPRECISION\n\n MessageText:\n\n  A specified precision was invalid\n',
  DB_E_BADSCALE: 'DB_E_BADSCALE:\n\n MessageId: DB_E_BADSCALE\n\n MessageText:\n\n  A specified scale was invalid\n',
  DB_E_BADTABLEID: 'DB_E_BADTABLEID:\n\n MessageId: DB_E_BADTABLEID\n\n MessageText:\n\n  Invalid table ID\n',
  DB_E_BADTYPE: 'DB_E_BADTYPE:\n\n MessageId: DB_E_BADTYPE\n\n MessageText:\n\n  A specified type was invalid\n',
  DB_E_DUPLICATECOLUMNID: 'DB_E_DUPLICATECOLUMNID:\n\n MessageId: DB_E_DUPLICATECOLUMNID\n\n MessageText:\n\n  A column ID was occurred more than once in the specification\n',
  DB_E_DUPLICATETABLEID: 'DB_E_DUPLICATETABLEID:\n\n MessageId: DB_E_DUPLICATETABLEID\n\n MessageText:\n\n  The specified table already exists\n',
  DB_E_TABLEINUSE: 'DB_E_TABLEINUSE:\n\n MessageId: DB_E_TABLEINUSE\n\n MessageText:\n\n  The specified table was in use\n',
  DB_E_NOLOCALE: 'DB_E_NOLOCALE:\n\n MessageId: DB_E_NOLOCALE\n\n MessageText:\n\n  The specified locale ID was not supported\n',
  DB_E_BADRECORDNUM: 'DB_E_BADRECORDNUM:\n\n MessageId: DB_E_BADRECORDNUM\n\n MessageText:\n\n  The specified record number is invalid\n',
  DB_E_BOOKMARKSKIPPED: 'DB_E_BOOKMARKSKIPPED:\n\n MessageId: DB_E_BOOKMARKSKIPPED\n\n MessageText:\n\n  Although the bookmark was validly formed, no row could be found to\n  match it\n',
  DB_E_BADPROPERTYVALUE: 'DB_E_BADPROPERTYVALUE:\n\n MessageId: DB_E_BADPROPERTYVALUE\n\n MessageText:\n\n  The value of a property was invalid\n',
  DB_E_INVALID: 'DB_E_INVALID:\n\n MessageId: DB_E_INVALID\n\n MessageText:\n\n  The rowset was not chaptered\n',
  DB_E_BADACCESSORFLAGS: 'DB_E_BADACCESSORFLAGS:\n\n MessageId: DB_E_BADACCESSORFLAGS\n\n MessageText:\n\n  Invalid accessor\n',
  DB_E_BADSTORAGEFLAGS: 'DB_E_BADSTORAGEFLAGS:\n\n MessageId: DB_E_BADSTORAGEFLAGS\n\n MessageText:\n\n  Invalid storage flags\n',
  DB_E_BYREFACCESSORNOTSUPPORTED: 'DB_E_BYREFACCESSORNOTSUPPORTED:\n\n MessageId: DB_E_BYREFACCESSORNOTSUPPORTED\n\n MessageText:\n\n  By-ref accessors are not supported by this provider\n',
  DB_E_NULLACCESSORNOTSUPPORTED: 'DB_E_NULLACCESSORNOTSUPPORTED:\n\n MessageId: DB_E_NULLACCESSORNOTSUPPORTED\n\n MessageText:\n\n  Null accessors are not supported by this provider\n',
  DB_E_NOTPREPARED: 'DB_E_NOTPREPARED:\n\n MessageId: DB_E_NOTPREPARED\n\n MessageText:\n\n  The command was not prepared\n',
  DB_E_BADACCESSORTYPE: 'DB_E_BADACCESSORTYPE:\n\n MessageId: DB_E_BADACCESSORTYPE\n\n MessageText:\n\n  The specified accessor was not a parameter accessor\n',
  DB_E_WRITEONLYACCESSOR: 'DB_E_WRITEONLYACCESSOR:\n\n MessageId: DB_E_WRITEONLYACCESSOR\n\n MessageText:\n\n  The given accessor was write-only\n',
  DB_SEC_E_AUTH_FAILED: 'DB_SEC_E_AUTH_FAILED:\n\n MessageId: DB_SEC_E_AUTH_FAILED\n\n MessageText:\n\n  Authentication failed\n',
  DB_E_CANCELED: 'DB_E_CANCELED:\n\n MessageId: DB_E_CANCELED\n\n MessageText:\n\n  The change was canceled during notification; no columns are changed\n',
  DB_E_CHAPTERNOTRELEASED: 'DB_E_CHAPTERNOTRELEASED:\n@@@+ V2.0\n\n MessageId: DB_E_CHAPTERNOTRELEASED\n\n MessageText:\n\n  The rowset was single-chaptered and the chapter was not released\n',
  DB_E_BADSOURCEHANDLE: 'DB_E_BADSOURCEHANDLE:\n\n MessageId: DB_E_BADSOURCEHANDLE\n\n MessageText:\n\n  Invalid source handle\n',
  DB_E_PARAMUNAVAILABLE: 'DB_E_PARAMUNAVAILABLE:\n\n MessageId: DB_E_PARAMUNAVAILABLE\n\n MessageText:\n\n  The provider cannot derive parameter info and SetParameterInfo has\n  not been called\n',
  DB_E_ALREADYINITIALIZED: 'DB_E_ALREADYINITIALIZED:\n\n MessageId: DB_E_ALREADYINITIALIZED\n\n MessageText:\n\n  The data source object is already initialized\n',
  DB_E_NOTSUPPORTED: 'DB_E_NOTSUPPORTED:\n\n MessageId: DB_E_NOTSUPPORTED\n\n MessageText:\n\n  The provider does not support this method\n',
  DB_E_MAXPENDCHANGESEXCEEDED: 'DB_E_MAXPENDCHANGESEXCEEDED:\n\n MessageId: DB_E_MAXPENDCHANGESEXCEEDED\n\n MessageText:\n\n  The number of rows with pending changes has exceeded the set limit\n',
  DB_E_BADORDINAL: 'DB_E_BADORDINAL:\n\n MessageId: DB_E_BADORDINAL\n\n MessageText:\n\n  The specified column did not exist\n',
  DB_E_PENDINGCHANGES: 'DB_E_PENDINGCHANGES:\n\n MessageId: DB_E_PENDINGCHANGES\n\n MessageText:\n\n  There are pending changes on a row with a reference count of zero\n',
  DB_E_DATAOVERFLOW: 'DB_E_DATAOVERFLOW:\n\n MessageId: DB_E_DATAOVERFLOW\n\n MessageText:\n\n  A literal value in the command overflowed the range of the type of\n  the associated column\n',
  DB_E_BADHRESULT: 'DB_E_BADHRESULT:\n\n MessageId: DB_E_BADHRESULT\n\n MessageText:\n\n  The supplied HRESULT was invalid\n',
  DB_E_BADLOOKUPID: 'DB_E_BADLOOKUPID:\n\n MessageId: DB_E_BADLOOKUPID\n\n MessageText:\n\n  The supplied LookupID was invalid\n',
  DB_E_BADDYNAMICERRORID: 'DB_E_BADDYNAMICERRORID:\n\n MessageId: DB_E_BADDYNAMICERRORID\n\n MessageText:\n\n  The supplied DynamicErrorID was invalid\n',
  DB_E_PENDINGINSERT: 'DB_E_PENDINGINSERT:\n\n MessageId: DB_E_PENDINGINSERT\n\n MessageText:\n\n  Unable to get visible data for a newly-inserted row that has not\n  yet been updated\n',
  DB_E_BADCONVERTFLAG: 'DB_E_BADCONVERTFLAG:\n\n MessageId: DB_E_BADCONVERTFLAG\n\n MessageText:\n\n  Invalid conversion flag\n',
  DB_E_BADPARAMETERNAME: 'DB_E_BADPARAMETERNAME:\n\n MessageId: DB_E_BADPARAMETERNAME\n\n MessageText:\n\n  The given parameter name was unrecognized\n',
  DB_E_MULTIPLESTORAGE: 'DB_E_MULTIPLESTORAGE:\n\n MessageId: DB_E_MULTIPLESTORAGE\n\n MessageText:\n\n  Multiple storage objects can not be open simultaneously\n',
  DB_E_CANTFILTER: 'DB_E_CANTFILTER:\n\n MessageId: DB_E_CANTFILTER\n\n MessageText:\n\n  The requested filter could not be opened\n',
  DB_E_CANTORDER: 'DB_E_CANTORDER:\n\n MessageId: DB_E_CANTORDER\n\n MessageText:\n\n  The requested order could not be opened\n',
  MD_E_BADTUPLE: 'MD_E_BADTUPLE:\n@@@+ V2.0\n\n MessageId: MD_E_BADTUPLE\n\n MessageText:\n\n  Bad tuple\n',
  MD_E_BADCOORDINATE: 'MD_E_BADCOORDINATE:\n\n MessageId: MD_E_BADCOORDINATE\n\n MessageText:\n\n  Bad coordinate\n',
  MD_E_INVALIDAXIS: 'MD_E_INVALIDAXIS:\n\n MessageId: MD_E_INVALIDAXIS\n\n MessageText:\n\n  The given aixs was not valid for this Dataset\n',
  MD_E_INVALIDCELLRANGE: 'MD_E_INVALIDCELLRANGE:\n\n MessageId: MD_E_INVALIDCELLRANGE\n\n MessageText:\n\n  One or more of the given cell ordinals was invalid\n',
  DB_E_NOCOLUMN: 'DB_E_NOCOLUMN:\n\n MessageId: DB_E_NOCOLUMN\n\n MessageText:\n\n  The supplied columnID was invalid\n',
  DB_E_COMMANDNOTPERSISTED: 'DB_E_COMMANDNOTPERSISTED:\n\n MessageId: DB_E_COMMANDNOTPERSISTED\n\n MessageText:\n\n  The supplied command does not have a DBID\n',
  DB_E_DUPLICATEID: 'DB_E_DUPLICATEID:\n\n MessageId: DB_E_DUPLICATEID\n\n MessageText:\n\n  The supplied DBID already exists\n',
  DB_E_OBJECTCREATIONLIMITREACHED: 'DB_E_OBJECTCREATIONLIMITREACHED:\n\n MessageId: DB_E_OBJECTCREATIONLIMITREACHED\n\n MessageText:\n\n  The maximum number of Sessions supported by the provider has \n  already been created. The consumer must release one or more \n  currently held Sessions before obtaining a new Session Object\n',
  DB_E_BADINDEXID: 'DB_E_BADINDEXID:\n\n MessageId: DB_E_BADINDEXID\n\n MessageText:\n\n  The index ID is invalid\n',
  DB_E_BADINITSTRING: 'DB_E_BADINITSTRING:\n\n MessageId: DB_E_BADINITSTRING\n\n MessageText:\n\n  The initialization string specified does not conform to specificiation\n',
  DB_E_NOPROVIDERSREGISTERED: 'DB_E_NOPROVIDERSREGISTERED:\n\n MessageId: DB_E_NOPROVIDERSREGISTERED\n\n MessageText:\n\n  The OLE DB root enumerator did not return any providers that \n  matched any of the SOURCES_TYPEs requested\n',
  DB_E_MISMATCHEDPROVIDER: 'DB_E_MISMATCHEDPROVIDER:\n\n MessageId: DB_E_MISMATCHEDPROVIDER\n\n MessageText:\n\n  The initialization string specifies a provider which does not match the currently active provider\n',
  SEC_E_BADTRUSTEEID: 'SEC_E_BADTRUSTEEID:\n\n MessageId: SEC_E_BADTRUSTEEID\n\n MessageText:\n\n  Invalid trustee value\n',
  SEC_E_NOTRUSTEEID: 'SEC_E_NOTRUSTEEID:\n\n MessageId: SEC_E_NOTRUSTEEID\n\n MessageText:\n\n  The trustee is not for the current data source\n',
  SEC_E_NOMEMBERSHIPSUPPORT: 'SEC_E_NOMEMBERSHIPSUPPORT:\n\n MessageId: SEC_E_NOMEMBERSHIPSUPPORT\n\n MessageText:\n\n  The trustee does not support memberships/collections\n',
  SEC_E_INVALIDOBJECT: 'SEC_E_INVALIDOBJECT:\n\n MessageId: SEC_E_INVALIDOBJECT\n\n MessageText:\n\n  The object is invalid or unknown to the provider\n',
  SEC_E_NOOWNER: 'SEC_E_NOOWNER:\n\n MessageId: SEC_E_NOOWNER\n\n MessageText:\n\n  No owner exists for the object\n',
  SEC_E_INVALIDACCESSENTRYLIST: 'SEC_E_INVALIDACCESSENTRYLIST:\n\n MessageId: SEC_E_INVALIDACCESSENTRYLIST\n\n MessageText:\n\n  The access entry list supplied is invalid\n',
  SEC_E_INVALIDOWNER: 'SEC_E_INVALIDOWNER:\n\n MessageId: SEC_E_INVALIDOWNER\n\n MessageText:\n\n  The trustee supplied as owner is invalid or unknown to the provider\n',
  SEC_E_INVALIDACCESSENTRY: 'SEC_E_INVALIDACCESSENTRY:\n\n MessageId: SEC_E_INVALIDACCESSENTRY\n\n MessageText:\n\n  The permission supplied in the access entry list is invalid\n',
  DB_S_ROWLIMITEXCEEDED: 'DB_S_ROWLIMITEXCEEDED:\n\n MessageId: DB_S_ROWLIMITEXCEEDED\n\n MessageText:\n\n  Fetching requested number of rows would have exceeded total number\n  of active rows supported by the rowset\n',
  DB_S_COLUMNTYPEMISMATCH: 'DB_S_COLUMNTYPEMISMATCH:\n\n MessageId: DB_S_COLUMNTYPEMISMATCH\n\n MessageText:\n\n  One or more column types are incompatible; conversion errors will\n  occur during copying\n',
  DB_S_TYPEINFOOVERRIDDEN: 'DB_S_TYPEINFOOVERRIDDEN:\n\n MessageId: DB_S_TYPEINFOOVERRIDDEN\n\n MessageText:\n\n  Parameter type information has been overridden by caller\n',
  DB_S_BOOKMARKSKIPPED: 'DB_S_BOOKMARKSKIPPED:\n\n MessageId: DB_S_BOOKMARKSKIPPED\n\n MessageText:\n\n  Skipped bookmark for deleted or non-member row\n',
  DB_S_NONEXTROWSET: 'DB_S_NONEXTROWSET:\n@@@+ V2.0\n\n MessageId: DB_S_NONEXTROWSET\n\n MessageText:\n\n  There are no more rowsets\n',
  DB_S_ENDOFROWSET: 'DB_S_ENDOFROWSET:\n\n MessageId: DB_S_ENDOFROWSET\n\n MessageText:\n\n  Reached start or end of rowset or chapter\n',
  DB_S_COMMANDREEXECUTED: 'DB_S_COMMANDREEXECUTED:\n\n MessageId: DB_S_COMMANDREEXECUTED\n\n MessageText:\n\n  The provider re-executed the command\n',
  DB_S_BUFFERFULL: 'DB_S_BUFFERFULL:\n\n MessageId: DB_S_BUFFERFULL\n\n MessageText:\n\n  Variable data buffer full\n',
  DB_S_NORESULT: 'DB_S_NORESULT:\n\n MessageId: DB_S_NORESULT\n\n MessageText:\n\n  There are no more results\n',
  DB_S_CANTRELEASE: 'DB_S_CANTRELEASE:\n\n MessageId: DB_S_CANTRELEASE\n\n MessageText:\n\n  Server cannot release or downgrade a lock until the end of the\n  transaction\n',
  DB_S_GOALCHANGED: 'DB_S_GOALCHANGED:\n@@@+ V2.5\n\n MessageId: DB_S_GOALCHANGED\n\n MessageText:\n\n  Specified weight was not supported or exceeded the supported limit\n  and was set to 0 or the supported limit\n',
  DB_S_UNWANTEDOPERATION: 'DB_S_UNWANTEDOPERATION:\n@@@+ V1.5\n\n MessageId: DB_S_UNWANTEDOPERATION\n\n MessageText:\n\n  Consumer is uninterested in receiving further notification calls for\n  this reason\n',
  DB_S_DIALECTIGNORED: 'DB_S_DIALECTIGNORED:\n\n MessageId: DB_S_DIALECTIGNORED\n\n MessageText:\n\n  Input dialect was ignored and text was returned in different\n  dialect\n',
  DB_S_UNWANTEDPHASE: 'DB_S_UNWANTEDPHASE:\n\n MessageId: DB_S_UNWANTEDPHASE\n\n MessageText:\n\n  Consumer is uninterested in receiving further notification calls for\n  this phase\n',
  DB_S_UNWANTEDREASON: 'DB_S_UNWANTEDREASON:\n\n MessageId: DB_S_UNWANTEDREASON\n\n MessageText:\n\n  Consumer is uninterested in receiving further notification calls for\n  this reason\n',
  DB_S_ASYNCHRONOUS: 'DB_S_ASYNCHRONOUS:\n@@@+ V1.5\n\n MessageId: DB_S_ASYNCHRONOUS\n\n MessageText:\n\n  The operation is being processed asynchronously\n',
  DB_S_COLUMNSCHANGED: 'DB_S_COLUMNSCHANGED:\n\n MessageId: DB_S_COLUMNSCHANGED\n\n MessageText:\n\n  In order to reposition to the start of the rowset, the provider had\n  to reexecute the query; either the order of the columns changed or\n  columns were added to or removed from the rowset\n',
  DB_S_ERRORSRETURNED: 'DB_S_ERRORSRETURNED:\n\n MessageId: DB_S_ERRORSRETURNED\n\n MessageText:\n\n  The method had some errors; errors have been returned in the error\n  array\n',
  DB_S_BADROWHANDLE: 'DB_S_BADROWHANDLE:\n\n MessageId: DB_S_BADROWHANDLE\n\n MessageText:\n\n  Invalid row handle\n',
  DB_S_DELETEDROW: 'DB_S_DELETEDROW:\n\n MessageId: DB_S_DELETEDROW\n\n MessageText:\n\n  A given HROW referred to a hard-deleted row\n',
  DB_S_TOOMANYCHANGES: 'DB_S_TOOMANYCHANGES:\n@@@+ V2.5\n\n MessageId: DB_S_TOOMANYCHANGES\n\n MessageText:\n\n  The provider was unable to keep track of all the changes; the client\n  must refetch the data associated with the watch region using another\n  method\n',
  DB_S_STOPLIMITREACHED: 'DB_S_STOPLIMITREACHED:\n\n MessageId: DB_S_STOPLIMITREACHED\n\n MessageText:\n\n  Execution stopped because a resource limit has been reached; results\n  obtained so far have been returned but execution cannot be resumed\n',
  DB_S_LOCKUPGRADED: 'DB_S_LOCKUPGRADED:\n\n MessageId: DB_S_LOCKUPGRADED\n\n MessageText:\n\n  A lock was upgraded from the value specified\n',
  DB_S_PROPERTIESCHANGED: 'DB_S_PROPERTIESCHANGED:\n\n MessageId: DB_S_PROPERTIESCHANGED\n\n MessageText:\n\n  One or more properties were changed as allowed by provider\n',
  DB_S_ERRORSOCCURRED: 'DB_S_ERRORSOCCURRED:\n\n MessageId: DB_S_ERRORSOCCURRED\n\n MessageText:\n\n  Errors occurred\n',
  DB_S_PARAMUNAVAILABLE: 'DB_S_PARAMUNAVAILABLE:\n\n MessageId: DB_S_PARAMUNAVAILABLE\n\n MessageText:\n\n  A specified parameter was invalid\n',
  DB_S_MULTIPLECHANGES: 'DB_S_MULTIPLECHANGES:\n\n MessageId: DB_S_MULTIPLECHANGES\n\n MessageText:\n\n  Updating this row caused more than one row to be updated in the\n  data source\n',
}