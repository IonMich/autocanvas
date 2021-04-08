import pandas as pd
from canvasapi.paginated_list import PaginatedList


def df_from_api_list(api_list, drop_requester=True, drop_created_at=True, 
                    set_index_id=True, bring_to_front="name"):
    """
    Convert list from API (i.e. `list(PaginatedList)` or 
    simply PaginatedList) to pandas by extracting all the 
    attributes of each object 
    
    Note: index might be lost if you perform merging at a later point, 
    so if you want to preserve it, use `set_index_id` to False.
    
    TODO: add the object itself in a column so that the dataframe can 
    still be used directly to extract more info.
    """ 
    if isinstance(api_list, PaginatedList):
        api_list = list(api_list)
    
    row_list = []
    for api_obj in api_list:
        row_list.append(api_obj.__dict__)
    df = pd.DataFrame(row_list)
    df["object"] = api_list
    
    if drop_requester:
        df = df.drop("_requester", errors="ignore", axis=1)
    if drop_created_at:
        df = df.drop("created_at", errors="ignore", axis=1)
    if set_index_id:
        df = df.set_index("id")
    if bring_to_front is not None:
        df = df[ [bring_to_front] + [col for col in df.columns 
                                        if col != bring_to_front] 
               ]
    return df

def series_from_api_object(api_object, 
                           add_object=True,
                           drop_requester=True, 
                           drop_created_at=True):
    """
    Convert object retrieved from API (i.e. to pandas by extracting all its
    attributes
    
    TODO: add the object itself in a row so that the dataframe can 
    still be used directly to extract more info.
    """ 
    
    series = pd.Series(api_object.__dict__)
    if add_object:
        series["object"] = api_object
    if drop_requester:
            series = series.drop("_requester", errors="ignore")
    if drop_created_at:
            series = series.drop("created_at", errors="ignore")
    return series