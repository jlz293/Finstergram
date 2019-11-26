# Finstergram
Introduction to Databases Fall 2019 Project

Team:

Sally Thompson, Anuska Rungta, Jason Zilberkweit 


# Part 3.1a
SELECT photoID FROM Photo WHERE photoID IN 
(SELECT photoID FROM Follow JOIN Photo ON Follow.username_followed = Photo.photoPoster WHERE allFollowers = 1 AND username_follower = ‘TestUser’) OR 
photoID IN (SELECT photoID FROM SharedWith WHERE groupName IN (SELECT groupName FROM BelongTo WHERE member_username = ‘TestUser’)) 

# Part 3.1b
Flask Server Side Code --> init.py
HTML Sites --> Templates 
Images --> static

# Part 3.2a: Demo Video
https://www.youtube.com/watch?v=T7-vWIWHvFQ


# Part 3.2b
Feature 4 
•	ManageFollows
•	Add a Boolean called acceptedFollow into Follow

Extra features
1.	Like photo: Anuska --> 	
    Add num_of_likes into Photo Table
    
2.	Unfollow: Sally

3.	Add comments: Jason --> 
    Add comments into Photo Table
    
    Create Table Comments ( 
    username VARCHAR(20),
    photoID int, 
    commenttime DATETIME,
    PRIMARY KEY(username, photoID),
    FOREIGN KEY(username) REFERENCES Person(username),
    FOREIGN KEY(photoID) REFERENCES Photo(photoID)
    );
    
4.	Add friend: Anuska

5.	Add friendGroup: Sally

6.	Which user has highest followers: Jason





