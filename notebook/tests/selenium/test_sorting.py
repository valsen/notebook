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
        'label': a.text
    } for a in browser.find_elements_by_class_name('item_name')]

def test_all_sorting(authenticated_browser):
    number_of_items = 3
    #gets all buttons used to sort files 
    buttons = get_buttons(authenticated_browser)   
    #assuming such notebooks exist as set in conftest.py
    my_labels = ["My Notebook 1.ipynb", "My Notebook 2.ipynb", "My Notebook 10.ipynb"]
    notebook_list = generate_list(authenticated_browser, my_labels, number_of_items)
    #assert initial natural sort: 1, 2, 10
    assert_correct_sort(notebook_list, my_labels, [0, 1, 2])
    counter = 0
    namebutton = 0
    #clicks in order: Name, Last Modified, File size
    for button in buttons:
        button['button'].click()
        if counter == 0:
            namebutton = button['button']
            #order should now be 10, 2, 1
            notebook_list = generate_list(authenticated_browser, my_labels, number_of_items)
            assert_correct_sort(notebook_list, my_labels, [2, 1, 0])
        if counter == 1:
            #order should now be 10, 1, 2
            notebook_list = generate_list(authenticated_browser, my_labels, number_of_items)
            assert_correct_sort(notebook_list, my_labels, [1, 2, 0])
            
            button['button'].click()
            #order should now be 2, 1, 10
            notebook_list = generate_list(authenticated_browser, my_labels, number_of_items)
            assert_correct_sort(notebook_list, my_labels, [1, 0, 2])
        if counter == 2: 
            #order should now be based on previous button clicks (since file size is unchanged), therefore 2, 1, 10
            notebook_list = generate_list(authenticated_browser, my_labels, number_of_items)
            assert_correct_sort (notebook_list, my_labels, [1, 0, 2])

            button['button'].click()
            #order should remain the same, 2, 1, 10
            notebook_list = generate_list(authenticated_browser, my_labels, number_of_items)
            assert_correct_sort (notebook_list, my_labels, [1, 0, 2])
        counter +=1
    namebutton.click()
    #assert name sorting works when the appropriate button is clicked again
    notebook_list = generate_list(authenticated_browser, my_labels, number_of_items)
    #assert initial natural sort: 1, 2, 10
    assert_correct_sort(notebook_list, my_labels, [0, 1, 2])


def test_letters_between_numbers(authenticated_browser):
    number_of_items = 3
    buttons = get_buttons(authenticated_browser)
    #assuming such files exist as set in conftest.py
    my_labels = ["t1es1t.txt", "t2es2t.txt", "t10es10t.txt"]
    notebook_list = generate_list(authenticated_browser, my_labels, number_of_items)
    #assert initial natural sort: t1est1, t2es2t, te10st
    assert_correct_sort(notebook_list, my_labels, [0, 1, 2])
    buttons[0]['button'].click()
    notebook_list = generate_list(authenticated_browser, my_labels, number_of_items)
    #assert initial natural sort: te10st, te2st, te1st
    assert_correct_sort(notebook_list, my_labels, [2, 1, 0])
    
    
def test_numbers_periods(authenticated_browser):
    number_of_items = 3
    buttons = get_buttons(authenticated_browser)
    #assuming such files exist as set in conftest.py
    my_labels = ["0.1.0.txt", "20.0.1.txt", "0201.0.0.txt"]
    notebook_list = generate_list(authenticated_browser, my_labels, number_of_items)
    #assert expected results 0201.0.0, 20.0.1, 0.1.0.txt weird naming conventions may lead to unclear situations
    #reverse order since button was clicked in test_sorting_letters_beteween_numbers
    assert_correct_sort(notebook_list, my_labels, [2, 1, 0])
    buttons[0]['button'].click()
    notebook_list = generate_list(authenticated_browser, my_labels, number_of_items)
    #assert initial natural sort:  0.1.0, 20.0.1, 0201.0.   0
    assert_correct_sort(notebook_list, my_labels, [0, 1, 2])
    

def test_numbers_between_letters(authenticated_browser):
    number_of_items = 3
    #assuming such files exist as set in conftest.py
    my_labels = ["test10hej.1.txt", "test2hej.1a.txt", "test2hej.txt"]
    notebook_list = generate_list(authenticated_browser, my_labels, number_of_items)
    #assert expected results test2hej.txt, test2hej.1a.txt, test10hej.1.txt weird naming conventions may lead to unclear situations
    assert_correct_sort(notebook_list, my_labels, [2, 1, 0])

def test_same_name_different_extensions(authenticated_browser):
    number_of_items = 5
    #assuming such files exist as set in conftest.py
    my_labels = ["1.txt", "1.doc", "1.docx", "1.rtf", "1.py"]
    notebook_list = generate_list(authenticated_browser, my_labels, number_of_items)
    #assert doc, docx, py, rtf, txt
    assert_correct_sort(notebook_list, my_labels, [4,0,1,3,2])

def test_many_potential_extensions(authenticated_browser):
    number_of_items = 3
    my_labels = ['1.txt.txt.doc', '1.txt.doc.doc', '1.txt.doc.txt']
    notebook_list = generate_list(authenticated_browser, my_labels, number_of_items)
    #assert txt.doc.doc, txt.doc.txt, txt.txt.doc
    assert_correct_sort(notebook_list, my_labels, [2,0,1])
 
def test_file_with_extension_compared_to_file_with_no_extension(authenticated_browser):
    number_of_items = 2
    my_labels = ['a', 'a.txt']
    notebook_list = generate_list(authenticated_browser, my_labels, number_of_items)
    #assert a before a.txt
    assert_correct_sort(notebook_list, my_labels, [0, 1])
    
#returns a generated list of the sorting buttons
def get_buttons(authenticated_browser):
    buttons = [{
    'button': a
    } for a in authenticated_browser.find_elements_by_class_name('sort_button')]    
    return buttons

#returns a generated list of the current order of items in my_labels
def generate_list(authenticated_browser, my_labels, number_of_items):
    items = get_list_items(authenticated_browser)
    notebook_list = []
    for item in items: 
        for label in my_labels:
            if label == item['label']:
                notebook_list.append(item['label'])
    return notebook_list

#to be used to assert that the items in notebook_list are in the expected order
def assert_correct_sort(notebook_list, my_labels, positions_notebook_list):
    counter = 0
    for position in positions_notebook_list:
        assert notebook_list[position] == my_labels[counter]
        counter += 1
    
