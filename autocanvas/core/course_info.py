import pandas as pd
import re
from .conversions import series_from_api_object, df_from_api_list

day_abbrs = ("M", "T", "W", "R", "F")


class Periods():
    def __init__(self, start_time, duration, timedelta, num_periods):
        self.start_time = start_time
        self.duration = duration
        self.timedelta = timedelta
        self.num_periods = num_periods
        self.start_times = self.get_start_times()
        self.end_times = self.get_end_times()
        
    @classmethod
    def Fall(cls):
        start_time = "07:25:00"
        duration = "00:50:00"
        timedelta = "01:05:00"
        num_periods = 11
        return cls(start_time, duration, timedelta, num_periods)
    
    @classmethod
    def Spring(cls):
        return cls.Fall()
    
    @classmethod
    def SummerC(cls):
        start_time = "08:00:00"
        duration = "01:05:00"
        timedelta = "01:30:00"
        num_periods = 7
        return cls(start_time, duration, timedelta, num_periods)
    
    @classmethod
    def SummerA(cls):
        start_time = "08:00:00"
        duration = "01:15:00"
        timedelta = "01:30:00"
        num_periods = 7
        return cls(start_time, duration, timedelta, num_periods)
    
    @classmethod
    def SummerB(cls):
        return cls.SummerA()
    
    @classmethod
    def Summer(cls):
        return cls.SummerC()
    
    @classmethod
    def from_season(cls, season):
        for method_name  in cls.__dict__:
            if method_name.lower()==season.lower():
                return getattr(cls, method_name)()
        else:
            raise ValueError("Constructor not found for this season")
    
    def get_start_times(self):
        base_date = "1980-1-1"
        return pd.date_range(start=base_date + " " + self.start_time, 
                              periods=self.num_periods, 
                              freq=pd.to_timedelta(self.timedelta))
    def get_end_times(self):
        return self.start_times + pd.to_timedelta(self.duration)        
    
    def get_dataframe(self):
        start = self.start_times.to_frame(index=False, name='start_times')
        end = self.end_times.to_frame(index=False, name='end_times')
        df_periods = (pd.merge(left=start,right=end, 
                        left_index=True, right_index=True)
                      .applymap(lambda item:item.time())
                     )
        df_periods.index = range(1,len(df_periods)+1)
        df_periods.index.name = "Period"
        return df_periods


def get_PHY_course(canvas, course_code, semester, course_id=None):
    myself = canvas.get_current_user()
    mycourses = myself.get_courses()
    # if we know the course ID is easy
    if course_id is not None:
        return canvas.get_course(course_id)
    # if we don't know the course ID we try to identify it from its name
    for course in mycourses:
        try:
            if (course_code in course.name) and (semester in course.name):
                return course
        except AttributeError:
            continue
    
    return None


def get_assignment_group_from_name(course, group_name):
    """
    canvas organizes assignments in groups
    e.g. discussion/"Recitation quizzes"
    """

    assignment_groups = course.get_assignment_groups()

    for assignment_group in assignment_groups:
        if (group_name.lower() in assignment_group.name.lower()):
            return assignment_group
    else:
        message = ("Assignment group name '{}' was not found!\n\n"
                    .format(group_name)+
                  "Use get_assignment_groups(course) "+
                  "to see all available assignment groups")
        raise ValueError(message)
        
    return None
    

def get_teaching_personel(course, add_first_name=True, 
                          groups=["ta", "teacher"]):
    """The list of TAs returned by Canvas might 
    include more teaching personel than simply the 
    TAs who teach sections 
    """
    result = []
    for group in groups:
        type_list = [group]
        users = course.get_users(enrollment_type=type_list)

        df = df_from_api_list(users)
        
        if add_first_name:
            df["first_name"] = df["name"].apply(lambda x:str.split(x)[0])
        result.append(df)

    return result


def get_sections(course,
                 include_students=True,
                 add_class_number=True,
                 remove_empty=True, 
                 add_TA_info=True,
                 section_ta_csv=None
                 ):
    if include_students:
        sections = course.get_sections(include="students")
    else:
        sections = course.get_sections()
        
    df_sections = df_from_api_list(sections)
    
    if remove_empty:
        if not include_students:
            message = ("Need student info (incluse_students=True) "
                       "to identify empty section")
            raise NotImplementedError(message)
        # Removing MISC and PHY2054
        df_sections = df_sections[~df_sections["students"].isnull()]
        df_sections = df_sections[~df_sections["name"].str.contains("-MISC")]
    if add_class_number:
        df_sections["class_number"] = (df_sections["name"]
                                          .str.extract(r'\w+\((\d+)', 
                                                       expand=True)
                                         ).astype(int)
        if add_TA_info:
            if section_ta_csv is not None:
                df_section_ta = pd.read_csv(section_ta_csv)[["class_number",
                                                            "section_ta_name"]]
                df_sections = pd.merge(left=df_sections, right=df_section_ta, 
                                       how="inner", on="class_number", 
                                       validate="1:1")
                
            else:
                raise FileNotFoundError("CSV file with class number and ta_name is required.")
                
    
    return df_sections
    
    
def get_students_from_sections(course, **kwargs):
    """
    Get students for each section.
    Optionally add class_number and ta_name  
    """
    
    
    df_sections = get_sections(course, 
                               include_students=True,
                               **kwargs)
    
    df_students = pd.DataFrame()
    for row in df_sections.iterrows():
        df_section_studs = pd.DataFrame(row[1].students)
        if "class_number" in df_sections.columns:
            df_section_studs["class_number"] = \
                        row[1].get("class_number",None)
            if "section_ta_name" in df_sections.columns:
                df_section_studs["section_ta_name"] = \
                        row[1].get("section_ta_name",None)
        df_students = pd.concat([df_students, df_section_studs])
    
    return df_students, df_sections

