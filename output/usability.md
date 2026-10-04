# Usability Improvements

## Backend

### 1. Search speed (t-shirt search took ~15s)

Originally, when I tested it, just asking for a t-shirt took 15 seconds. This is too long for a customer to wait just to see the search results, and they might just leave the webpage if it takes too long. Making it faster helps to keep customers attention and show them their results faster. The AI was able to get it down to 3 seconds, apparently with an "Azure/Portkey network floow of 1.5s". Even though ideally it would be faster, that is still a 80% decrease in load time. 

Apparently when I fixed this, Claude removed the tool registrations from the agent. After recieving homework 2 feedback, I told Claude that the agent needed to have tool registrations, and I tried to go back to improving the speed in an alternate way. That brought the timing back up to 5-6 seconds, which is still better than the 15 seconds that it initially took. 

### 2. Search accuracy ("blue crew necks" returned blue hoodies)
When searching for something as simple as blue crew necks, the page was showing blue hoodies and no crew necks even though there are crew necks in stock. If a customer doesn't find what they're looking for when they search, they might get confused and then choose to not buy anyting. 

## Frontend

### 1. Add to wishlist
Once someone finds an item that they like, they can't actually do anything with that item. At first I told the AI to create an add to cart feature which is what most online shopping websites have, but since in this case, I wouldn't be creating a whole checkout process for the website, I changed it to be an updated wishlist that the user is able to save and use as a reference when they go to the store in person. When expanding on this website in the future, it will be easy to convert the wishlist page to an cart page, and add the functionality for actually checking out. 

### 2. Sort (price / color / item type)
I added a sort by drop down for featured, price, color and item type so that if the customer wants to peruse the whole product list with some specific criteria in mind, they are able to sort by that. This feature makes it easier to browse the whole catalogue even if someone doesn't know exactly what they want to search by. 

### 3. Create account — last name field alignment
The create account form was misaligned, so I wanted to fix the alignment. This wasn't a functionallity fix, it was purely a visual fix, but makes the website look more professional and put together.
