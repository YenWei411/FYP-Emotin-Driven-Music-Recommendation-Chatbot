import json
from tkinter import Tk, Label, Entry, Button, Text, Scrollbar, END, Frame, ttk, Toplevel, messagebox
from textblob import TextBlob
import nltk
import random
import pandas as pd

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    
try:
    from textblob.download_corpora import main
    main()
except nltk.exceptions.ContentRetrievalError:
    print("Error downloading Corpora.")
    
class ChatbotApp:
    def __init__(self, master):
        self.master = master
        master.title("EmoTune")
        self.last_analyzed_emotion = None  # Variable to store the last analyzed emotion
        
        #set whole window pane
        self.frame = Frame(master, padx=100, pady=100)
        self.frame.pack()
        # master.attributes('-fullscreen', True)
        
        title_label = Label(self.frame, text="EMOTUNE", font=("Arial", 24, "bold italic"))
        title_label.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky='nsew')
        
        self.chat_history = Text(self.frame, wrap='word', height=22, width=70, state='disabled')
        self.chat_history.grid(row=1, column=0, columnspan=4, padx=10, pady=10, sticky='nsew')
        self.reset_button = ttk.Button(self.frame, text='Reset', command=self.reset_text)
        self.master.bind('<F5>', self.reset_text)
        self.reset_button.grid(row=2, column=3, padx=10, pady=(0, 10), sticky='ew')
        
        #Ask for user input
        self.label = ttk.Label(self.frame, text="\t      Your Text: " ,font=("Arial", 13))
        self.label.grid(row=3, column=0, sticky='w')
        self.entry = ttk.Entry(self.frame, width=50)
        self.entry.focus_set()
        self.entry.grid(row=3, column=1, padx=10, pady=(0, 10), sticky='ew')
        self.input_analysis = ttk.Label(self.frame, text="Song Recommendation: ",font=("Arial", 13))
        self.input_analysis.grid(row=4, column=0, sticky='w')
        self.analysis_result = Text(self.frame, wrap='word', height=10, width=50, state='disabled')
        self.analysis_result.grid(row=4, column=1, padx=10, pady=(0, 10), sticky='ew')
        self.enter_button = ttk.Button(self.frame, text='Enter', command=self.analyze_text)
        self.master.bind('<Return>', lambda event: self.analyze_text())
        self.enter_button.grid(row=3, column=3, padx=10, pady=(0, 10), sticky='ew')
        self.btn_closeprogram = ttk.Button(self.frame, text='Exit EmoTune', command=self.close_program)
        self.master.bind('<Escape>', self.close_program)
        self.btn_closeprogram.grid(row=4, column=3, padx=10, pady=(0, 10), sticky='ew')
        
        #Scrollbar for sentiment and recommend song output
        self.scrollbar = Scrollbar(self.frame, command=self.chat_history.yview)
        self.scrollbar.grid(row=1, column=4, sticky='ns')
        self.anal_scrollbar = Scrollbar(self.frame, command=self.chat_history.yview)
        self.anal_scrollbar.grid(row=4, column=4, sticky='ns')
        self.chat_history.config(yscrollcommand=self.scrollbar.set)
        self.analysis_result.config(yscrollcommand=self.anal_scrollbar.set)
        
        # Load data from CSV
        data = pd.read_csv('MusicMoodFinal.csv')
        self.data = data
        self.mooddata = data[['Mood', 'artists','name']]
        self.responses = self.load_responses_from_file('chatbot_response.json')
        
        #Define welcome message
        self.clean_chat_history()
        WELCOME_MESSAGE = "EmoTune: Welcome to EmoTune! I'm here to help you analyze your sentiment and recommend songs based on your emotion."
        with open('chat_history.txt', 'a') as file:
            file.write(f"{WELCOME_MESSAGE}\n")
        # Initialize chat history with welcome message
        self.refresh_chat_history()
        
    #Define emotion categories
    EMOTION_CATEGORIES = {'Sad': ['Sad'],'Energetic': ['Energetic'],
                          'Calm': ['Calm'],'Happy': ['Happy']} 

    # Define polarity threshold for classifying positive/negative sentiment
    POLARITY_THRESHOLD = 0.2
    
    # Define subjectivity threshold for classifying neutral sentiment
    SUBJECTIVITY_THRESHOLD = 0.5
            
    def analyze_text(self):
        user_input = self.entry.get()
        if not user_input:
            output_message = ('You have not input any sentences. Start by talking to EmoTune first!')
            messagebox.showinfo('Info', output_message)
        else:
            # Analyze sentiment
            sentiment, polarity, subjectivity, analysis = self.analyze_sentiment(user_input)
            explanation = self.generate_explanation(sentiment, polarity, subjectivity)
            emotion = self.classify_emotion(sentiment, polarity, subjectivity)
            output_message = f"Sentiment: {sentiment}\n\nPolarity: {polarity:.2f}\n\nSubjectivity: {subjectivity:.2f}\n\nEmotion: {emotion}\n\nExplanation:{explanation}"
            print(output_message)
            self.last_analyzed_emotion = emotion            
            # Generate chatbot response
            chatbot_response = self.generate_chatbot_response(user_input)
                  
            # Append user input and chatbot response to chat history
            with open('chat_history.txt', 'a') as file:
                file.write(f"    You: {user_input}\n")
                file.write(f"EmoTune: {chatbot_response}\n")
            self.refresh_chat_history()
            self.recommend_songs()
            self.entry.delete(0, 'end')            
            
    def display_recommend_result(self):
        self.analysis_result.config(state='normal')
        self.analysis_result.delete(1.0, END)
        with open('recommendsongs.txt', 'r') as file:
            song_recommend = file.read()
        self.analysis_result.insert(END, song_recommend)
        self.analysis_result.config(state='disabled')
            
    def clean_chat_history(self):
        with open('chat_history.txt', 'w') as file:
            file.write('')
        self.refresh_chat_history()
    
    # Display chat history in the text field
    def refresh_chat_history(self):
        self.chat_history.config(state='normal')
        self.chat_history.delete(1.0, END)
        with open('chat_history.txt', 'r') as file:
            chat_history_content = file.read()
        self.chat_history.insert('end', chat_history_content)
        # self.chat_history.config(state='disabled')
        self.chat_history.yview(END)
    
    # Function to load responses from file
    def load_responses_from_file(self, file_path):
            with open(file_path, 'r') as file:
                data = json.load(file)
            return {item['tag']: {'patterns': item['patterns'], 'responses': item['responses']} for item in data}
        
    def generate_chatbot_response(self, user_input):
        for tag, data in self.responses.items():
            for pattern in data['patterns']:
                if pattern.lower() in user_input.lower():
                    return random.choice(data['responses'])
        return "I'm sorry, I don't understand. But here are some song recommendations to you still." 
    
    #Recommend songs base on the emotion from analyzed emotion
    def recommend_songs(self):
        if self.last_analyzed_emotion:
            if self.last_analyzed_emotion in self.EMOTION_CATEGORIES:
                songs_data = self.mooddata[self.mooddata['Mood'].isin(self.EMOTION_CATEGORIES[self.last_analyzed_emotion])]
                songs = [f"{song['name']} by {song['artists']}" for index, song in songs_data.iterrows()]
                random_songs = random.sample(songs, min(len(songs), 10))  # Get up to 5 random songs                
                with open('recommendsongs.txt', 'w') as file:
                    file.write(f"EmoTune: I have analyze your emotion as {self.last_analyzed_emotion}\n")
                    file.write(f"\nHere are some songs that matches your feelings\n")
                    for song in random_songs:
                        file.write(f"- {song}\n\n")
                self.display_recommend_result()  # Refresh chat history to display changes
        else:
            no_song_alert = ("You have not input any sentences. EmoTune can't recommend you songs. Start by talking to EmoTune first!")
            messagebox.showinfo('Info', no_song_alert)

    
    #Classify emotion using sentiment, polarity, subjectivity
    def classify_emotion(self, sentiment, polarity, subjectivity):
        if sentiment == 'Positive':
            if polarity > self.POLARITY_THRESHOLD:
                if subjectivity > self.SUBJECTIVITY_THRESHOLD:
                    return 'Happy'  # High positive polarity and subjectivity
                else:
                    return 'Energetic'  # High positive polarity but low subjectivity
            else:
                return 'Calm'  # Positive sentiment with low polarity
        elif sentiment == 'Negative':
            if polarity < -self.POLARITY_THRESHOLD:
                if subjectivity > self.SUBJECTIVITY_THRESHOLD:
                    return 'Sad'  # High negative polarity and subjectivity
                else:
                    return 'Sad'  # High negative polarity but low subjectivity
            else:
                return 'Calm'  # Negative sentiment with low polarity
        else:  # Neutral sentiment
            if subjectivity > self.SUBJECTIVITY_THRESHOLD:
                return 'Energetic'  # Neutral sentiment with high subjectivity
            else:   
                return 'Calm'  # Neutral sentiment with low subjectivity    
            
    #reset all text data
    def reset_text(self):
        self.entry.delete(0, 'end')
        self.chat_history.config(state='normal')
        self.chat_history.delete(1.0, END)
        self.chat_history.config(state='disabled')
        self.analysis_result.config(state='normal')
        self.analysis_result.delete(1.0, END)
        self.analysis_result.config(state='disabled')
        self.last_analyzed_emotion = None
        self.clean_chat_history()
        WELCOME_MESSAGE = "EmoTune: Welcome to EmoTune! I'm here to help you analyze your sentiment and recommend songs based on your emotion."
        with open('chat_history.txt', 'a') as file:
            file.write(f"{WELCOME_MESSAGE}\n")
        self.refresh_chat_history()
        
    
    #analyze user input sentiment
    def analyze_sentiment(self, text):
        analysis = TextBlob(text)
        polarity, subjectivity = analysis.sentiment.polarity, analysis.sentiment.subjectivity
        sentiment = 'Positive' if polarity > 0 else 'Negative'if polarity <0 else 'Neutral'
        return sentiment, polarity, subjectivity, analysis
    
    # use sentiment polarity and subjectivity to explain
    def generate_explanation(self, sentiment, polarity, subjectivity):
        explanation = f" The sentiment of the text is {sentiment.lower()}. "
        explanation += (
            f"\nIt generally expresses a {'positive' if sentiment == 'Positive' else 'negative'}"
            f"\nThe polarity score is {polarity:.2f}, where a higher value indicates a stronger positive or negative sentiment expressed in the text."
            f"\nThe subjectivity score is {subjectivity:.2f}, where a higher value indicates the text is more subjective and opinionated."
        )
        return explanation
    
    def close_program(self):
        #Hide master window
        self.master.withdraw()
        # Create a new window for confirmation
        confirmation_window = Toplevel(self.master)
        confirmation_window.title("Close EmoTune")
        confirmation_window.geometry("300x300")
        Label(confirmation_window, text="\n\n\n\n\nDo you want to exit EmoTune?").pack()
        # Center the window
        confirmation_window.update_idletasks()
        width = confirmation_window.winfo_width()
        height = confirmation_window.winfo_height()
        x_offset = (confirmation_window.winfo_screenwidth() - width) // 2
        y_offset = (confirmation_window.winfo_screenheight() - height) // 2
        confirmation_window.geometry(f"{width}x{height}+{x_offset}+{y_offset}")
        
        # Function to handle 'Yes' button click
        def on_yes_click():
            # Clear chat history
            self.clean_chat_history()
            # Close confirmation window
            confirmation_window.destroy()
            # Open feedback window
            feedback_window = Toplevel(self.master)
            feedback_window.title("EmoTune Feedback")
            feedback_window.geometry("300x300")

            # Function to handle saving feedback
            def save_feedback():
                feedback_text = feedback_entry.get()
                with open('feedbacks.txt', 'a') as file:
                    file.write(f"{feedback_text}\n")
                feedback_window.destroy()
                self.master.destroy()            
            # Create text and entry for feedback
            Label(feedback_window, text="\n\n\n\nThank you for using Emotune").pack()
            Label(feedback_window, text="How do you think about EmoTune?\n").pack()           
            feedback_entry = ttk.Entry(feedback_window, width=40)
            feedback_entry.pack(anchor='center')
            # Create button to save feedback
            Label(feedback_window, text="").pack()
            ttk.Button(feedback_window, text="Submit", command=save_feedback).pack()
            # Center the window
            feedback_window.update_idletasks()
            width = feedback_window.winfo_width()
            height = feedback_window.winfo_height()
            x_offset = (feedback_window.winfo_screenwidth() - width) // 2
            y_offset = (feedback_window.winfo_screenheight() - height) // 2
            feedback_window.geometry(f"{width}x{height}+{x_offset}+{y_offset}")

        # Function to handle 'No' button click
        def on_no_click():
            confirmation_window.destroy()
            # Show the master window again
            self.master.deiconify()

        # Create 'Yes' and 'No' buttons
        btn_yes = ttk.Button(confirmation_window, text='Yes', command=on_yes_click)
        btn_no = ttk.Button(confirmation_window, text='No', command=on_no_click)
        
        # Calculate the width of each button
        btn_width = max(len(btn_yes["text"]), len(btn_no["text"])) + 150  # Add some padding

        # Place the buttons in the center with space between them
        btn_yes.place(relx=0.5, rely=0.5, anchor='center', x=btn_width // 2 - 5)
        btn_no.place(relx=0.5, rely=0.5, anchor='center', x=-btn_width // 2 + 5)
    
if __name__ == "__main__":
    root = Tk()
    app = ChatbotApp(root)
    root.mainloop()