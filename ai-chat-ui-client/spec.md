You are a coding assistant, whose task is to create a AI conversational UI Chat Client using REACT. Below are the features to be developed:

- Add a chat input box in the bottom of the UI, where user can input prompt/instructions. 
- The chat input box must have the send button with icon paper aeroplane to send the user input to backend API.
- The header of the page should have a `New Chat` button to initiate a new chat and clear the input and other sections as mentioned below.
- The middle section must be left to render the user and assistant chats in alternate rows with left for assistant, right for assistant.
- The assistant messages would come from a backend API, which would be a stream API with text tokens, so UI must render them as they arrive.