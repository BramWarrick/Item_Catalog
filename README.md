## Table of Contents
* Installation
* High Level Structure
* Rationale


## Installation

* Navigate to desired directory for git clone and run code below:
	* `git clone https://github.com/BramWarrick/Item_Catalog.git`
* Add client_secrets.json file to directory using directions on this webpage:
	* https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
* Run the main.py file to activate the web service using one of the following ways:
	* Open main.py in Sublime and press ctrl+b to start.
	* In windows, with Python 2.7 installed, navigate to the directory and enter "main.py" and press enter
	* In Bash, navigate to the directory and enter "main.py" and press enter
* Using a browser of your choice, navigate to localhost:5000 and log in.
* Once logged in, the New Item and New Category options are in the upper right after logging in.


## High Level Structure

Users own Item Categories, which in turn hold Items with their descriptions  

### APIs
| URI                                    | JSON Information                 |
|----------------------------------------|----------------------------------|
| /category/<int:category_id>/JSON       | Listing of single category       |
| /category/<int:category_id>/items/JSON | Listing of all items in category |
| /category/JSON                         | Listing of all categories        |

### User interaction
| URI                                | Page                           |
|------------------------------------|--------------------------------|
| /category/new                      | Create new category            |
| /category/<int:category_id>/edit/  | Manage and edit user category  |
| /category/<int:category_id>        | Category contents listed       |
| /item/new                          | Create new item                |
| /item/<int:item_id>/edit/          | Edit item                      |


## Rationale

Specs were largely uncomplicated regarding the treatment of categories and items, so I kept this aspect fairly clean.  
  
User can create categories and items with the ability to fully edit them at any point. UI is clean and familiar for any creation or edits.  
  
Google's OAuth 2.0 was implemented for user creation and log in with information saved in the Users table.  