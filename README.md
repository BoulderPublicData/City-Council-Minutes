# City Council Minutes
This project transcribes the Signed Minutes for Boulder's City Council into a semi-structured format.

## Data format
A reverse chronological list of meeting documents. 

### meeting documents
A `meeting` document is a dictionary with top-level keys:
* date - the date of the meeting as an ISO-8601 YYYY-MM-DD string
* minutes_url - a URL of the signed minutes document
* attendees - the last names of city council members in attendance as a list of strings
* open_comment - a list of `comment` documents
* consent_agenda - a `consent_agenda` document
* callup_checkin - topics that are called up from boards and commissions as a list of strings
* public_hearings - a list of `hearing` documents

### comment documents
A `comment` document is a dictionary with two keys:
* name - the name of the speaker
* topic - the summary of the topic

### consent_agenda documents
A `consent_agenda` document is a dictionary with items and votes:
* items - ordered items on the consent agenda as a list of strings
* yeas - the last names of council members voting Yes/Yea as a list of strings
* nays - the last names of council members voting Nay/No as a list of strings
* absent - the last names of council members voting absent or abstaining as a list of strings

### hearing documents
A `hearing` document is a dictionary with information about hearings:
* name - a name of the ordinance, resolution, or motion as a string
* description - a description of the hearing topic as a string
* speakers - the full names of speakers at the hearing as a list of strings
* motion - the last name of the council member introducing the motion as a string
* seconded - the last name of the council member introducing the motion as a string
* yeas - the last names of council members voting Yes/Yea as a list of strings
* nays - the last names of council members voting Nay/No as a list of strings
* absent - the last names of council members voting absent or abstaining as a list of strings

### Example meeting document
```
// A document for a meeting
  {
  // Enter the date of the meeting as a YYYY-MM-DD string
  date: 
  
  // Enter the URL where the meeting minutes live as a string
  minutes_url: 
  
  // Enter the last names of the city council members in attendance as a list
  attendees:[

    ]
    
  // Enter the names and topics of speakers during open comment as a list of dictionaries
  open_comment:[
      {
      name: 
      topic: 
      }
    ]
    
  // Enter the topics of the consent agenda as a dictionary with items, yeas, nays, absences
  consent_agenda:{
    items:[]
    yeas:[]
    nays:[]
    absent:[]
    }
    
  // Enter the items called up from other boards and commissions as a list of strings
  callup_checkin:[

    ]
    
  // Enter the public hearings as a list of dictionaries
  public_hearings:[

      // The first hearing dictionary
      {
      name: 
      description: 
      opened: 
      closed: 
      speakers: [
        
        ],
      motion: 
      seconded: 
      yeas: []
      nays: []
    }
    ]
}
```

## Validation
A [HJSON](https://hjson.github.io/) file is hosted [here](https://json.link/D6f2H0KntI) that generates the [JSON file](https://json.link/wGiTx3N5w2.json).
