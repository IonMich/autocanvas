from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import re
from bs4 import BeautifulSoup
import pandas as pd
from os.path import join
import time
from selenium.common.exceptions import NoSuchElementException



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
    
    general_filter_ids = ["term", "category", "prog-level", "dept"]
    option_texts = [semester, program, program_level, department]
    options_dict = dict(zip(general_filter_ids, option_texts))
    
    max_wait_sec = 10
    
    
    for element_id, option_text in options_dict.items():
        element = WebDriverWait(driver, max_wait_sec).until(
            EC.presence_of_element_located((By.ID, element_id))
        )
        select = Select(element)
        select.select_by_visible_text(option_text)

    course_filter_ids = ["course-number", "course-title", "instructor"]
    input_texts = [course_code, course_title, instructor]
    inputs_dict = dict(zip(course_filter_ids, input_texts))
    
    # TODO: click only if expand==False:
#     driver.find_element_by_id("general-filter-header").click()
    
    for element_id, input_text in inputs_dict.items():
        driver.find_element_by_id(element_id).send_keys(input_text)
    else:
        driver.find_element_by_id(element_id).send_keys("\n")

    # Wait for course to appear
    course_element = WebDriverWait(driver, max_wait_sec).until(
        lambda x: x.find_element_by_id("sect0")) 
#     course_element.click()
    
    df = get_section_info_from_course_element(
        driver, 
        course_element, 
        last_person_is_TA=last_person_is_TA,
        only_first_meeting_is_lecture=only_first_meeting_is_lecture)
    
    ufsoc_course_html = course_element.get_attribute("outerHTML")
    
#     ufsoc_course_html = driver.find_element_by_id("sect0").get_attribute("outerHTML")
#     df = get_section_info_from_html(
#                     ufsoc_html=ufsoc_course_html,
#                     driver=driver,
#                     last_person_is_TA=last_person_is_TA,
#                     only_first_meeting_is_lecture=only_first_meeting_is_lecture)
    return df, ufsoc_course_html, driver

def get_section_info_from_course_element(driver, 
                                         course_element, 
                                         last_person_is_TA=True,
                                         only_first_meeting_is_lecture=True):
    max_wait_sec = 10
    all_section_info = []
    sections = course_element.find_elements_by_xpath("./div")
    for section in sections:
#         print(section.text)
        
        items = WebDriverWait(driver, max_wait_sec).until(
                      lambda x: section.find_elements_by_xpath("./div"))
        time.sleep(0.3)
        class_number_div , details_div = items
#         print(class_number_div.text)
        class_number = re.findall(r"Class #\s*(\d{5})", 
                                  class_number_div.text)[0]
        
        left_side_div, right_side_div = details_div.find_elements_by_xpath("./div")
        meeting_times_div = left_side_div.find_elements_by_xpath("./div")[0]
        meetings = meeting_times_div.find_elements_by_xpath("./div")
        
        meeting_names = ["meeting_" + str(idx+1) 
                         for idx in range(len(meetings))]
        if only_first_meeting_is_lecture:
            meeting_names[0] = "lecture_times"
        meeting_times = []
        for meeting in meetings:
            meeting = meeting.find_element_by_xpath("./div/div")
            meeting_days, meeting_period, _ = meeting.find_elements_by_xpath("./div")
            meeting_days = re.findall(r"(.*)\|", meeting_days.text)[0].strip()
            meeting_period = re.findall(r"Period (\d+)",meeting_period.text)[0]
            meeting_time = "{} | Period {}".format(meeting_days, meeting_period)
            meeting_times.append(meeting_time)
            
            
        meetings_dict = dict(zip(meeting_names, meeting_times))
#         print(meetings_dict)
        
        teaching_personel_div = right_side_div.find_elements_by_xpath("./div/div")[0]
        teaching_personel_div = teaching_personel_div.find_element_by_xpath("./div/div")
        try:
            teaching_personel_link = teaching_personel_div.find_element_by_tag_name("a")
            teaching_personel_link.click()
            max_wait_sec = 10
            instructors_dialog = WebDriverWait(driver, max_wait_sec).until(
                      lambda x: x.find_element_by_id(
                          "instructors-dialog-description"
                      ))
            teaching_personel_p = WebDriverWait(driver, max_wait_sec).until(
                lambda x: instructors_dialog.find_elements_by_tag_name("p"))
            
            time.sleep(0.1)
            teaching_personel = [person.text for person in teaching_personel_p]
#             print(teaching_personel)
            webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        except NoSuchElementException:
            teaching_personel = teaching_personel_div.find_elements_by_tag_name("p")
            teaching_personel = [person.text for person in teaching_personel]
#             print(teaching_personel)
        teaching_personel_col_names = ["instuctor_"+str(idx+1) 
                                       for idx in range(len(teaching_personel))]
        
        if last_person_is_TA:
            teaching_personel_col_names[-1] = "section_ta_name"
        teaching_personel_dict = dict(zip(teaching_personel_col_names, 
                                          teaching_personel))
        
        all_section_info.append({
                        **{
                    "class_number":class_number,
                        }, 
                        **teaching_personel_dict,
                        **meetings_dict,})
#         print(section)
    return pd.DataFrame(all_section_info)
    

def get_section_info_from_html(ufsoc_html, driver=None, last_person_is_TA=True, 
                               only_first_meeting_is_lecture=True):
    """
    DEPRICATED. Switched from bs4 to pure Selenium
    # TODO: get room info (e.g. TBA, WEB, NPB 1001, etc.)
    # only regular NPB xxxx seems to appear as text.
    """
        
    soup = BeautifulSoup(ufsoc_html, features="lxml")
    sections = soup.find_all("div", {"class": "MuiPaper-root sc-XhUvE kpvYZt MuiPaper-outlined MuiPaper-rounded"})
    
    all_section_info = []
    for section in sections:
        # uncomment to troubleshoot
        # print(section)
        # Class number
        class_number_div , details_div = \
                        section.find_all('div', recursive=False)
        class_number = re.findall(r"Class #\s*(\d{5})", 
                                  class_number_div.text)[0]
        
        left_side_div, right_side_div = details_div.find_all('div', 
                                                             recursive=False)
        # Meeting times
        meeting_times_div = left_side_div.find_all('div', recursive=False)[0]
        meetings = meeting_times_div.find_all('div', recursive=False)
        meeting_names = ["meeting_" + str(idx+1) 
                         for idx in range(len(meetings))]
        if only_first_meeting_is_lecture:
            meeting_names[0] = "lecture_times"
        meeting_times = []
        for meeting in meetings:
            text = meeting.text.replace("\xa0", "")
            meeting_days, meeting_period = re.findall(r"(.*)\|.*Period (\d+)", 
                                                         text
                                                     )[0]
            meeting_time = "{} | Period {}".format(meeting_days, meeting_period)
            meeting_times.append(meeting_time)

        meetings_dict = dict(zip(meeting_names, meeting_times))
        
        # Teaching Personel
        teaching_personel_div = right_side_div.find_all("div", recursive=True)[3]
        teaching_personel_link = teaching_personel_div.find("a",recursive=True)
        if driver and teaching_personel_link:
            driver.find_elements_by_link_text(
                teaching_personel_link.text).click()
            max_wait_sec = 10
            instructors_dialog = WebDriverWait(driver, max_wait_sec).until(
                      lambda x: x.find_element_by_id(
                          "instructors-dialog-description"
                      ))
            teaching_personel_p = WebDriverWait(driver, max_wait_sec).until(
                lambda x: instructors_dialog.find_elements_by_tag_name("p"))
            
            time.sleep(0.1)
            teaching_personel = [person.text for person in teaching_personel_p]
            print(teaching_personel)
            webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        else:
            teaching_personel = teaching_personel_div.find_all("p",recursive=True)
            teaching_personel = [person.text for person in teaching_personel]
            print(teaching_personel)
        teaching_personel_col_names = ["instuctor_"+str(idx+1) 
                                       for idx in range(len(teaching_personel))]
#         len_teaching_personel = len(teaching_personel)
#         print(len_teaching_personel)
#         teaching_personel = [person for person in teaching_personel]
#         teaching_personel_col_names = ["instuctor_"+str(idx+1) 
#                                        for idx in range(len_teaching_personel)]
        if last_person_is_TA:
            teaching_personel_col_names[-1] = "section_ta_name"
        teaching_personel_dict = dict(zip(teaching_personel_col_names, 
                                          teaching_personel))
        
        all_section_info.append({
                        **{
                    "class_number":class_number,
                        }, 
                        **teaching_personel_dict,
                        **meetings_dict,})
        
    return pd.DataFrame(all_section_info)


def store_section_ta_to_csv(output_dir=None, identifier=None,**kwargs):
    """
    """
    output_dir = '' if output_dir is None else str(output_dir)
    identifier = '' if identifier is None else str(identifier)
    if len(identifier)>0:
        if identifier[0] not in ["_", "-", "."]:
            identifier = "_" + identifier
    
    df, html, driver = get_sections_from_ufsoc(**kwargs)
    
    file_name = "sections" + identifier + ".csv"
    file_path = join(output_dir, file_name)
    print(file_path)
    df.to_csv(file_path, index=False)
    
    return df, html, driver


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