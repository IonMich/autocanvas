import pandas as pd
import re
import difflib
from bs4 import BeautifulSoup
from .conversions import series_from_api_object, df_from_api_list
from .course_info import (
    get_PHY_course, 
    get_assignment_group_from_name,)


def get_assignment(course, name=None, group=None, number=None,
                   object_id=None, ignore_makeup=False):
    
    
    if isinstance(name, str):
        all_assignments = course.get_assignments()
        df_all_assignments = df_from_api_list(all_assignments)
        assignment = df_all_assignments[df_all_assignments["name"]==name].copy()
        try:
            assignment["identifier_number"] = \
                (assignment["name"].str.extract(r'(\d+)').astype(int))
        except Exception as e:
            print(e)
    elif isinstance(group, str):
        if not isinstance(number, int):
            raise ValueError("if you specify group, you also need to specify number as int.")            
        
        df_assignments = get_assignment_collection(course,
                             assignment_group_name=group,
                             add_identifier_numbers=True
                            )
        assignment = df_assignments[
                df_assignments["identifier_number"]==number
        ]
        if ignore_makeup:
            assignment = assignment[~assignment.name.str
                                   .contains(pat=r"makeup",
                                             flags=re.IGNORECASE,
                                             regex=True)
                          ]
    else:
        raise ValueError("you need to pass either name or group as arguments")
        
    if len(assignment)>1:
        raise ValueError("Found Multiple assignments with these "+
                         "specifications: {}".format(assignment["name"]))
        
    return assignment



def get_assignment_submissions(assignment, 
                               df_students=None, 
                               df_TAs=None, 
                               include_submission_history=False):
    """This function assumes that students are divided into sections"""
    if isinstance(assignment, (pd.Series, pd.DataFrame)):
        assignment = assignment.get("object").iloc[0]
    if include_submission_history:
        assignment_submissions = \
                assignment.get_submissions(
                        include=["submission_history"]
        )
    else:
        assignment_submissions = assignment.get_submissions()
    df_subs = df_from_api_list(assignment_submissions, 
                              drop_created_at=False, 
                              bring_to_front="user_id")
    ## Remove Test student.
    # small todo: is there a safer way?
    df_subs = df_subs[:-1]
    
    # from now on we want to make sure we don't lose any submissions
    len_subs = len(df_subs)
    
    if (df_students is not None) and (df_TAs is not None):
        # adding course_section and section_ta_id
        df_subs = pd.merge(left=df_subs, right=df_students, 
                           left_on="user_id", right_on="id",
                           how="left",validate="m:1")
        df_subs = pd.merge(left=df_subs, 
                           right=(df_TAs.reset_index()[["id",
                                                        "name",
                                                        "object",
                                                        "first_name"]]
                                        .add_prefix("section_ta_")
                                 ), 
                           on="section_ta_name",
                           how="left", validate="m:1")
        assert len(df_subs)==len_subs, "Data were lost unexpectedly"
    
    # grader_id is less than 0 if the submission has been graded 
    # automatically. This can happen for a 
    mask = (df_subs.grader_id < 0) & (df_subs.workflow_state=="graded")
    len_auto = len(df_subs[mask])

    if len_auto>0:
        print("Warning! {} students appear to be autograded!".format(len_auto))
        if (df_students is not None):
            pass
#         The following line has a type error, so commented out
#             print(df_subs[mask].short_name)
        if (df_TAs is not None):
            print("Replacing grader_id with section_ta_id.")
            df_subs_valid = df_subs[mask]
            df_subs.loc[mask,"grader_id"] = df_subs_valid["section_ta_id"]
    
    if df_TAs is not None:
        # adding grader info
        df_subs = pd.merge(left=df_subs, right=df_TAs.add_prefix('grader_'), 
                           left_on="grader_id", right_on="id",
                           suffixes=(False,False),how="left")

        assert len(df_subs)==len_subs, "Data were lost unexpectedly"
    
    return df_subs


def get_assignment_collection(course,
                             assignment_group_name,
                             name_pattern=".*",
                             exclude_numbers=None,
                             add_identifier_numbers=True,
                             set_index_id=True,
                             title_column="name",
                             number_pattern='(\d+)'
                            ):
    """
    TODO: give examples for patterns in the docstring
    
    """
    assignment_group = get_assignment_group_from_name(
                            course, 
                            group_name=assignment_group_name)
        
    
    # This includes makeups and surveys
    assignments_list = course.get_assignments_for_group(
                                               assignment_group)
    df_assignments = df_from_api_list(assignments_list,
                                      set_index_id=set_index_id,
                                      bring_to_front=title_column)
    
    if name_pattern is not None:
        # Select assignements whose name is "Quiz ####" (one or more digits)
        df_assignments = df_assignments[df_assignments[title_column]
                                        .str.match(name_pattern)]
    if exclude_numbers is not None:
        # Exclude assignments that contain e.g. " 0", " 10", " 13" 
        # with a negative lookahead regex
        numbers_text = r"|".join([r" {}".format(x) for x in exclude_numbers])
        exclude_numbers_pattern = r"^((?!"+numbers_text+").)*$"
        df_assignments = df_assignments[df_assignments[title_column]
                                        .str.match(exclude_numbers_pattern)]
        
    if add_identifier_numbers:
        df_assignments["identifier_number"] = \
                (df_assignments[title_column]
                 .str.extract(number_pattern))
        df_assignments["identifier_number"] = \
                    pd.to_numeric(df_assignments["identifier_number"], 
                                  errors="coerce")
    
    return df_assignments


def get_assignment_groups(course):
    groups = df_from_api_list(
        course.get_assignment_groups()
    )
    return groups


def get_submissions_in_collection(assignment_collection, 
                                  df_students=None, 
                                  df_TAs=None,):
    """
    Gather all quiz submissions on a DataFrame.
    
    Very slow! Can be greatly improved with asyncio and aiohhtp.
    Do it in a way that still works (albeit slowly) even if 
    these packages are not installed.
    
    We might want to convert this to a single dataframe with MultiIndex
    """
    collection = assignment_collection.copy()
    collection["submissions"] = \
        collection["object"].apply(
             lambda x: get_assignment_submissions(assignment=x, 
                                       df_students=df_students, 
                                       df_TAs=df_TAs)
    )
    columns = ["name", 
               "identifier_number", 
               "object", 
               "submissions",]
    
    return collection[columns]


def get_graded_submissions(df_subs):
    """Ignoring missing and excused submissions
    
    Takes as input a DataFrame of submissions
    """
    df_graded = df_subs[(df_subs["workflow_state"]=="graded") &
                            (df_subs["excused"]!=1) &
                            (df_subs["missing"]!=1)
                           ].copy()
    return df_graded


def get_submitted_submissions(df_subs):
    """Ignoring missing and excused submissions
    
    Takes as input a DataFrame of submissions
    """
    df_submitted = df_subs[(df_subs["excused"]!=1) &
                        (df_subs["missing"]!=1)].copy()
    
    return df_submitted


def get_student_answers(df_submitted):
    assert "submission_history" in df_submitted.columns
    answers_list = []
    for index, submission in df_submitted.iterrows():
        user_id = submission.user_id
        student_name = submission["name"]
        assert len(submission.submission_history)==1
        assert submission.submission_history[-1]["submission_data"] is not None
        sub_data = submission.submission_history[-1]["submission_data"]
        for question_data in sub_data:
            question_data["user_id"] = user_id
            question_data["student_name"] = student_name
            answers_list.append(question_data)
    return pd.DataFrame(answers_list)


def get_quiz(course, title=None, group=None, number=None,
                   object_id=None, 
                   ignore_makeup=False):
    
    
    if isinstance(title, str):
        all_quizzes = course.get_quizzes()
        df_all_quizzes = df_from_api_list(all_quizzes, 
                                          bring_to_front=None)
        quiz = df_all_quizzes[df_all_quizzes["title"]==title].copy()
        try:
            quiz["identifier_number"] = \
                (quiz["title"].str.extract(r'(\d+)').astype(int))
        except Exception as e:
            print(e)
    else:
        raise NotImplementedError
    
    return quiz


def get_question_texts(df_questions):
    """input DataFrame can be retrieved by quiz.get_questions()"""
    
    return df_questions["question_text"].apply(lambda x : 
                                               BeautifulSoup(x, features="lxml").p)


def get_question_ids_from_text(text_list, question_texts, cutoff=0.3):
    question_ids = []
    closest_matches = []
    for text in text_list:
#         print(text)
        question_texts = question_texts.astype(str)
        closest_match = difflib.get_close_matches(text, question_texts, 
                                                  n=1, cutoff=cutoff)
#         print(closest_match)
        question_id = question_texts[question_texts.values==closest_match].index[0]
        question_ids.append(question_id)
        closest_matches.append(closest_match)
        
        
    return question_ids, closest_matches


def get_question_ids(text_list, df_questions, cutoff=0.3):
    """input DataFrame can be retrieved by quiz.get_questions()"""
    question_texts = get_question_texts(df_questions)
    
    question_ids, closest_matches = get_question_ids_from_text(text_list, 
                                                           question_texts, 
                                                           cutoff=cutoff)
        
        
    return question_ids, closest_matches