from .basic import *
from .creation import *
from .filtering import *
from .partitioning import *
from .reducing import *
from .zipping import *
from .transforms import *
from ..builtins import map, filter, zip

#
# Aliases
#

# countby = count_by
dropwhile = drop_while
groupby = group_by
# isdistinct = is_distinct
# isiterable = is_iterable
partitionby = partition_by
reduceby = reduce_by
takewhile = take_while
topk = top_k

#
# Removed/recipes
#

# toolz.first = nth(0)
# toolz.frequencies = collections.Counter
# toolz.rest = drop(1)
# toolz.second = nth(1)