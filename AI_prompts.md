# Homework 4 — AI Prompts

## Problem 1: Vibe Coder Prompts

### Prompt

ok now we will do homework 4 for AI class. start problem 1: vibe coder prompts. as with the other homewroks, create the AI_prompts.md file, in which you always paste verbatim the prompt that i sent, and any follow up prompts for each problem

### Follow-up Prompt

do not assume the assignment, i will provide step by step instructions of what needs to be done

## Problem 2: Analyze the Database

### Prompt

now problem 2: analyze the database. start a harness.md file that explains each table and the fields within that table with a short 1 line description

## Problem 3: Build the Campus Customs Website

### Prompt

problem 3: build the campus customs website
scaffold a react, typescript, vite frontend for campus customs. the nav bar at the top should have home, products, about us, log in, create account. use the information on their existing website to fill in home and about us. on the products page, show the product images using the image paths from the db. also display the item name, price and a short description from the db. each product should open as a single page item that has the image large on the left hand side,. the name of the product should be across the top, and then on the right, next to the picture, have the description, price, and sizes/available stock easy to click through. this single page should be visible when someone clicks on an item from the catalogue. on the bottom right of all pages, there should be a floating chat panel with a stubbed backend. the api to get all the info for the db should be called main.py and live in the backend folder

### Follow-up Prompt

do not copy and paste the text from the source sites. make sure it's original

## Problem 4: Create Account and Login

### Prompt

now let's do problem 4: create account and login
the create account page should ask for first and last name, email, password and then confirm the passwords. it should check that the passwords are the same, and that they meet minimum security requirements of being 10 characters long, having an uppercase letter and a number. new accounts should be stored in the users table, and passwords should be stored using a hashing algorithim so any bad actors cannot access user data. 
the login page should log in users that are in the user db table.
update harness.md to explain in simple terms what data is stored for the user and how the passwords are protected

### Follow-up Prompt

i should be able to login with this test user that has an email: test@campuscustoms.yale.edu and password: password
don't remove the test account

## Problem 5: Pydantic AI Backend

### Prompt

Problem 5: Pydantic AI backend
Now we want a shop chatbot made with PydanticAI and FastAPI for the chat panel. the api app should go in main.py and get run with Unvicorn. the agent will be in  four files (backend/prompts/prompt.md, backend/agent.py, backend/tools.py and backend/models.py which is where the structured types go) similar to the hw 3 structure. main.py should be able to return a reply from the agent when a message is sent to the chatbot by using the Portkey API key. 
prompt.md should include voice and safety basics - talk kindly to customers, do not talk about anything other than campus customs shop, and any other rules that make sense. 
models.py should have types for chat replies and product cards to make responses to users comprehensive. 
update harness.md to explain how the agent is loaded, and how the frontend interacts with FastAPI
this is how the backend should run: uvicorn main:app --reload --port 8000

## Problem 6: Tools — Product Info and Stock

### Prompt

problem 6: tools: product info and stock. the agent needs a tool in tools.py that gets the data from the db. the agent should never make up prices or any other data - add that to prompt. if soemthing is out of stock, share that with the user. expand the prompt.md file to know to use these tools, and update models.py to include the types. then list the tools in harness.md and add explanations for which model fields are being used for lookups

### Follow-up Prompt

move harness.md into output/harness.md

## Problem 7: Chat search that updates the page

### Prompt

problem 7. add a tool the allows the agent to search the catalogue based on the customer's question and dynamically show the items that are relevant as product cards. the agent should return structured product information that match the frontend view. the single item page should still work once the website products are filtered down based on the user's question. update prompt.md and harness.md to make it clear how search results appear on the page

### Follow-up Prompt

when i test it, there's a link that takes me to the new search page. i want the page to dynamically update based on the question the user asks

## Problem 8: Customer Memory

### Prompt

problem 8 customer memory
we want to set up the customer memory to have records of chat logs when a user is logged in. the agent should know the name and email of who is chatting which should be available through agent dependencies or a tool that the agent can call.  guests should still be bale to chat, but users should have saved chat history. 
also add page context that provides the agent with which products are currently on the page, so that if a customer asks a follow up question after their search, the agent can still help appropriately. 
update harness.md to explain how history is stored, what user fields the agent sees, and how page context is passed

## Problem 9: Usability Improvements

### Prompt

now problem 9. i have a few usability improvements i'd like to make 
first create output/usability.md for me to fill out
backend

1. when i ask the chatbot to show me t-shirts, it takes around 15 seconds to re-load the page. optimize the search algorithm and make the search faster.
2. when i asked for blue crew necks, the agent shows me 2 blue hoodies instead of showing the baseball left crewneck. there is clearly a misalignment in the search algoritm. reevaluate the algorithm and make it more accurate, and check a few similar edge cases. 

frontend

1. there is currently no add to cart feature - add an add to cart feature, with a page for the cart and the ability to add to cart and view the cart. 
2. add a sort function so that a user can sort by price, color, or item type 
3. on the create account page, the last name text box is shoved all the way to the right. center it more.

### Follow-up Prompt

Change the cart to a wishlist so that the user can see their wishlist and see what they had saved when they are actually in the store

### Follow-up Prompt

the functionality of the wishlist is weird across sizes. if i add a small, i am not able to add a medium of the same item. i should be able to do that.

### Follow-up Prompt

the chatbot still takes 7-8 seconds to load the results of the search. it should be around 1-2 seconds. this is incredibly important, and makes a huge difference in the company's success. without this quick search ability, the company will fail.

## Problem 10: Style the Website

### Prompt

problem 10 style the website
the design i'm going for is y2k inspired internet, but slightly modernized. keep the yale colors but use chrome, metallic, and electric blue accents. there should be fun badges and stickers used intentionally. the inspiration is glossy teen magazine meets apple website. make the chat look like you're speaking to Handsome Dan, Yale's mascot.

### Follow-up Prompt

make an output/design.md file for me to fill out


### Follow-up Prompt

The current design is too corporate and futuristic. The goal is for college students to be excited about buying these products, and Y2K is trending now. Do not use any corporate aesthetics. Focus on light and bright backgrounds, silver and blue chrome accents, metallic blue, holographic effects, tiny blue stars or other popular y2k icons, playful patterns. For headlines use a fun retro font but just use a regular font for everything else.

### Follow-up Prompt

The aesthetic is much better. Now the layout feels off with this design. Look at Y2K websites and take inspo from there - the hero banner at the top feels too modern with this visual aesthetic. Also add a small ticker bar with some of the new products instead of the featured section at the bottom.

### Follow-up Prompt

this is great improvement. the stickers shouldn't cover the text. also the stars in the background make it hard to read the main banner. the three boxes at the bottom feel out of place and not in line with this new aesthetic. none of the new feel and layout feels carried over to the other pages, it feels like it only exists on the same page.

## Problem 11: Site Check and Test

### Prompt

now problem 11 is a site check and test. i need to create a live document called app_check.html that documents my testing of this website. the screenshots that i reference will go in a folder called output/app_check_images and get linked in the html file with relative paths. add headings for the three scenarios i will be checking and adding screenshots for:

1. checking inventory level of an item through chat
2. dynamic search results after asking for hoodies
3. the wishlist, which was my usability addition from problem 9

### Follow-up Prompt

when i am trying to test this, the chat said it doesn't have color information for the products? this was working before.

### Follow-up Prompt

the app_check html has too much - it should just have the screenshots and short captions explaining the result of the test

### Follow-up Prompt

when i tried to test scenario 1, it said it doesn't have access to the inventory quantities. try running the test scenarios i shared to make sure that the search works as expected

### Follow-up Prompt

i tried to ask the chat how many there are and it's saying there is 1. shouldn't that prompt it to check the stock and return the values? if i ask how many there are, it should tell me the breakdown across sizes, not just that there is 1 type of shirt. i want this behavior to be implied nad obvious even if the user asks a slightly different question

### Follow-up Prompt

if the question is how many blue crew necks are there, that makes sense to answer differently, or respond to clarify which blue crewnecks, but if there is only one of that product type, it makes sense to jump straight into the inventory breakdown by size

## Problem 12: Audit Trail, Safety, and Finish Harness

### Prompt

problem 12 audit trail, safety, finish harness
create an append only audit trail of agent loop activity that stores time, tool name, args/result and stop reason. never wipe it. also add safety rules to prompt md (never take personal information, never give out personal information or someone else's chat history, and anything else that makes sense as an importnat safety rule)
also update harness.md to include everything that explains how the website works - models.py explanations, tools and abilities, safety, and important specs.

## Problem 13: Final Setup

### Prompt

now problem 13, we will do all the final set up. create a .env.example file, and a .gitignore file that makes sure the real env, db, and product images don't get pushed to github. also create README.md that explains how to run the frontend and backend after setting up a datapack. 

### Follow-up Prompt

on a previous homework assignment, i got feedback that my tools weren't registered correctly. check that the tools are registered correctly on this assignment. 

are there any other optimizations that can be done while keeping the tools registered