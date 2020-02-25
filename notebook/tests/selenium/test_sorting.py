import os
import io
from nbformat import write
from nbformat.v4 import new_notebook

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from notebook.utils import url_path_join
from notebook.tests.selenium.utils import wait_for_selector
pjoin = os.path.join


class PageError(Exception):
    """Error for an action being incompatible with the current jupyter web page.
    
    """
    def __init__(self, message):
        self.message = message
        

def url_in_tree(browser, url=None):
    if url is None:
        url = browser.current_url
    tree_url = url_path_join(browser.jupyter_server_info['url'], 'tree')
    return url.startswith(tree_url)


def get_list_items(browser):
    """Gets list items from a directory listing page
    
    Raises PageError if not in directory listing page (url has tree in it)
    """
    if not url_in_tree(browser):
        raise PageError("You are not in the notebook's file tree view."
                        "This function can only be used the file tree context.")
    # we need to make sure that at least one item link loads
    wait_for_selector(browser, '.item_link')

    return [{
        'label': a.find_element_by_class_name('item_name').text
    } for a in browser.find_elements_by_class_name('item_link')]

def test_all_sorting(authenticated_browser):
    #gets all buttons used to sort files 
    buttons = getButtons(authenticated_browser)   
    #assuming such notebooks exist as set in conftest.py
    myLabels = ["My Notebook 1.ipynb", "My Notebook 2.ipynb", "My Notebook 10.ipynb"]
    notebookList = generateList(authenticated_browser, myLabels)
    #assert initial natural sort: 1, 2, 10
    assertCorrectSort(notebookList, myLabels, 0, 1, 2)
    counter = 0
    namebutton = 0
    #clicks in order: Name, Last Modified, File size
    for button in buttons:
        button['button'].click()
        if counter == 0:
            namebutton = button['button']
            #order should now be 10, 2, 1
            notebookList = generateList(authenticated_browser, myLabels)
            assertCorrectSort(notebookList, myLabels, 2, 1, 0)
        if counter == 1:
            #order should now be 10, 1, 2
            notebookList = generateList(authenticated_browser, myLabels)
            assertCorrectSort(notebookList, myLabels, 1, 2, 0)
            
            button['button'].click()
            #order should now be 2, 1, 10
            notebookList = generateList(authenticated_browser, myLabels)
            assertCorrectSort(notebookList, myLabels, 1, 0, 2)
        if counter == 2: 
            #order should now be based on previous button clicks (since file size is unchanged), therefore 2, 1, 10
            notebookList = generateList(authenticated_browser, myLabels)
            assertCorrectSort (notebookList, myLabels, 1, 0, 2)

            button['button'].click()
            #order should remain the same, 2, 1, 10
            notebookList = generateList(authenticated_browser, myLabels)
            assertCorrectSort (notebookList, myLabels, 1, 0, 2)
        counter +=1
    namebutton.click()
    #assert name sorting works when the appropriate button is clicked again
    notebookList = generateList(authenticated_browser, myLabels)
    #assert initial natural sort: 1, 2, 10
    assertCorrectSort(notebookList, myLabels, 0, 1, 2)


def test_sorting_letters_between_numbers(authenticated_browser):
    buttons = getButtons(authenticated_browser)
    #assuming such files exist as set in conftest.py
    myLabels = ["t1es1t.txt", "t2es2t.txt", "t10es10t.txt"]
    notebookList = generateList(authenticated_browser, myLabels)
    #assert initial natural sort: t1est1, t2es2t, te10st
    assertCorrectSort(notebookList, myLabels, 0, 1, 2)
    buttons[0]['button'].click()
    notebookList = generateList(authenticated_browser, myLabels)
    #assert initial natural sort: te10st, te2st, te1st
    assertCorrectSort(notebookList, myLabels, 2, 1, 0)
    
    
def test_sorting_numbers_underscore(authenticated_browser):
    buttons = getButtons(authenticated_browser)
    #assuming such files exist as set in conftest.py
    myLabels = ["0.1.0.txt", "20.0.1.txt", "0201.0.0.txt"]
    notebookList = generateList(authenticated_browser, myLabels)
    #assert expected results 0201.0_0, 20.0_1, 0.1.0.txt weird naming conventions may lead to unclear situations
    #reverse order since button was clicked in test_sorting_letters_beteween_numbers
    assertCorrectSort(notebookList, myLabels, 2, 1, 0)
    buttons[0]['button'].click()
    notebookList = generateList(authenticated_browser, myLabels)
    #assert initial natural sort:  0.1_0, 20.0_1, 0201.0_0
    assertCorrectSort(notebookList, myLabels, 0, 1, 2)
    
#returns a generated list of the sorting buttons
def getButtons(authenticated_browser):
    buttons = [{
    'button': a
    } for a in authenticated_browser.find_elements_by_class_name('sort_button')]    
    return buttons

#returns a generated list of the current order of items in myLabels
def generateList(authenticated_browser, myLabels):
    items = get_list_items(authenticated_browser)
    notebookList = []
    for item in items: 
        if myLabels[0] == item['label'] or myLabels[1] == item['label'] or myLabels[2] == item['label']:
            notebookList.append(item['label'])
    return notebookList

#to be used to assert that the items in notebookList are in the expected order
def assertCorrectSort(notebookList, myLabels, a, b, c):
    assert notebookList[a] == myLabels[0]
    assert notebookList [b] == myLabels[1]
    assert notebookList[c] == myLabels[2]

    
