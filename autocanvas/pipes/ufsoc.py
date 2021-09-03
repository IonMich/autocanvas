from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
import re
from bs4 import BeautifulSoup
import pandas as pd
from os.path import join


def get_sections_from_ufsoc(semester,
                            course_code="PHY2054",
                            course_title="Physics 2",
                            instructor="",
                            department="Physics",
                            program="Campus / Web / Special Program",
                            program_level="Undergraduate",
                            url="https://one.uf.edu/soc/",
                            headless=True,
                            last_person_is_TA=True,
                            only_first_meeting_is_lecture=True
                           ):
    

    options = webdriver.ChromeOptions()
    # Set chrome to run without a head
    if headless:
        options.add_argument('headless')
    options.add_argument('window-size=1800,1200')
    # Initialize the driver
    driver = webdriver.Chrome(options=options)
    # This takes you to the schedule of courses
    driver.get(url)
    
    general_filter_ids = ["semes", "prog", "progLevel", "dep"]
    option_texts = [semester, program, program_level, department]
    options_dict = dict(zip(general_filter_ids, option_texts))

    for element_id, option_text in options_dict.items():
        select = Select(driver.find_element_by_id(element_id))
        # select by visible text
        select.select_by_visible_text(option_text)

    course_filter_ids = ["courseCode", "courseTitle", "instructor"]
    input_texts = [course_code, course_title, instructor]
    inputs_dict = dict(zip(course_filter_ids, input_texts))
    
    driver.find_element_by_id("courseFilters").click()
    for element_id, input_text in inputs_dict.items():
        driver.find_element_by_id(element_id).send_keys(input_text)
    else:
        driver.find_element_by_id(element_id).send_keys("\n")

    # Wait for course to appear
    max_wait_sec = 10
    course_element = WebDriverWait(driver, max_wait_sec).until(
        lambda x: x.find_element("xpath", '//*[@class="course-container ng-scope"]')) 
    course_element.click()
    
    ufsoc_course_html = driver.find_element_by_id("ufSOC").get_attribute("outerHTML")
    df = get_section_info_from_html(
                    ufsoc_html=ufsoc_course_html, 
                    last_person_is_TA=last_person_is_TA,
                    only_first_meeting_is_lecture=only_first_meeting_is_lecture)
    return df


def get_section_info_from_html(ufsoc_html, last_person_is_TA=True, 
                               only_first_meeting_is_lecture=True):
    """
    # TODO: get room info (e.g. TBA, WEB, NPB 1001, etc.)
    # only regular NPB xxxx seems to appear as text.
    """
        
    soup = BeautifulSoup(ufsoc_html, features="lxml")
    sections = soup.find_all("div", {"class": "section-tile ng-scope"})
    
    all_section_info = []
    for section in sections:
        # uncomment to troubleshoot
        # print(section)
        class_header = section.findChildren(
                        attrs={"class":
                               "course-subhead ng-binding ng-scope"}, 
                        recursive=True)[0].text
        class_number = re.findall(r"Class Number:\s*(\d{5})", class_header)[0]
        
        teaching_personel = section.findChildren(
                        attrs={"class":
                               "instructor-name ng-binding ng-scope"}, 
                        recursive=True)
        len_teaching_personel = len(teaching_personel)
        teaching_personel = [person.text for person in teaching_personel]
        teaching_personel_col_names = ["instuctor_"+str(idx+1) 
                                       for idx in range(len_teaching_personel)]
        if last_person_is_TA:
            teaching_personel_col_names[-1] = "section_ta_name"
        teaching_personel_dict = dict(zip(teaching_personel_col_names, 
                                          teaching_personel))
        
        meeting_elements = section.findChildren(attrs={"class":
                                                       "ng-binding ng-scope"}, 
                                                recursive=True)
        meeting_times = [element.text for element in meeting_elements 
                         if "|" in element.text]
        len_meetings = len(meeting_times)
        meeting_names = ["meeting_"+str(idx+1) for idx in range(len_meetings)]
        if only_first_meeting_is_lecture:
            meeting_names[0] = "lecture_times"

        meeting_dict = dict(zip(meeting_names, meeting_times))
        
#         # difficult to add room info, because it is not 
#         # recognized as text if it is online
#         meeting_rooms = [element.text for element in meeting_elements]
#         print(meeting_rooms)
        
        all_section_info.append({
                        **{
                    "class_number":class_number,
                        }, 
                        **teaching_personel_dict,
                        **meeting_dict,})
        
    return pd.DataFrame(all_section_info)


def store_section_ta_to_csv(output_dir=None, identifier=None,**kwargs):
    """
    """
    output_dir = '' if output_dir is None else str(output_dir)
    identifier = '' if identifier is None else str(identifier)
    if len(identifier)>0:
        if identifier[0] not in ["_", "-", "."]:
            identifier = "_" + identifier
    
    df = get_sections_from_ufsoc(**kwargs)
    
    file_name = "sections" + identifier + ".csv"
    file_path = join(output_dir, file_name)
    print(file_path)
    df.to_csv(file_path, index=False)
    
    return df


def parse_PHY_section_info(df):
    """
    NOT IMPLEMENTED
    goal is to interprete recitation session info
    
    difficult to separate the two. Ideas:
    - always identify lecture as meeting_1, while recitations is the rest
    - use Room Info to decide whether it is lecture or recitation
    """
    
    def parse_one_meeting(meeting_times_text):
        matches = re.findall(r"([A-Z])\s*\|\s*Period\s*(\d+)", 
                             meeting_times_text)
        if len(matches)!=1:
            raise ValueError("Need to have exactly one match, found: {}".format(len(matches)))
        day, period = matches[0][0], int(matches[0][1])

        return day, period

    def parse_two_meetings(meeting_times_text):
        matches = re.findall(r"([A-Z]),([A-Z])\s*\|\s*Period\s*(\d+)", meeting_times_text)
        if len(matches)!=1:
            raise ValueError("Need to have exactly one match, found: {}".format(len(matches)))
        day_1, day_2, period = matches[0][0], matches[0][1], int(matches[0][2])

        return day_1, day_2, period


    raise NotImplementedError
    
    
    
    if len_meetings not in [2, 3, 4]:
        raise NotImplementedError("Can not interpret meetings as lecture + recitations")

    hybrid_lectures = False if "," in meeting_times[0] else True
    hybrid_recitations = False if "," in meeting_times[-1] else True

    if not hybrid_recitations:
        recitation_day_1, recitation_day_2, recitation_period = \
                                    parse_two_meetings(meeting_times[-1])
    else:
        recitation_day_1, recitation_period_1 = \
                                    parse_one_meeting(meeting_times[-2])
        recitation_day_2, recitation_period = \
                                    parse_one_meeting(meeting_times[-1])
        if recitation_period_1 != recitation_period:
            raise NotImplementedError("Recitation periods need to be the same.")
    
        
    return None