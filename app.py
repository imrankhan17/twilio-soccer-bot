import re
import pandas as pd

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)


@app.route('/bot', methods=['POST'])
def bot():

    # read in data
    df = pd.read_csv('https://www.football-data.co.uk/mmz4281/1819/E0.csv')
    df['HomeTeam'] = df['HomeTeam'].str.lower()
    df['AwayTeam'] = df['AwayTeam'].str.lower()

    # make string lowercase and remove whitespace
    incoming_msg = request.values.get('Body', '').strip().lower()
    resp = MessagingResponse()
    msg = resp.message()

    if 'hello' in incoming_msg:
        reply = ("Hello and welcome to the English Premier League 2018/19 WhatsApp bot!\n\n"
                 "You can ask questions like:\n"
                 "- How many matches did Liverpool play?\n"
                 "- How many goals did Arsenal score?\n"
                 "- How many goals did Brighton score away from home?\n"
                 "- How many shots did West Ham concede?\n"
                 "- What was the result of Chelsea vs Everton?")

        msg.body(reply)
        return str(resp)

    # get list of teams and extract relevant team(s) mentioned in question
    all_teams = df['HomeTeam'].unique().tolist()
    team = re.findall('|'.join(all_teams), incoming_msg)

    if len(team) == 0:
        reply = "Sorry, we couldn't recognise any of the teams mentioned in your question."

    elif 'matches' in incoming_msg:
        # this question is about how many matches the team played
        result = len(df[(df['HomeTeam'] == team[0]) | (df['AwayTeam'] == team[0])])
        reply = f'{team[0].title()} played {result} matches.'

    elif 'goals' in incoming_msg:
        # this question is about how many goals the team scored at home, away or both

        if 'away' in incoming_msg:
            result = df[df['AwayTeam'] == team[0]]['FTAG'].sum()
            reply = f'{team[0].title()} scored {result} goals away from home.'

        elif 'home' in incoming_msg:
            result = df[df['HomeTeam'] == team[0]]['FTHG'].sum()
            reply = f'{team[0].title()} scored {result} goals at home.'

        else:
            result = df[df['HomeTeam'] == team[0]]['FTHG'].sum() + df[df['AwayTeam'] == team[0]]['FTAG'].sum()
            reply = f'{team[0].title()} scored {result} goals overall.'

    elif 'shots' in incoming_msg:
        # this question is about how many shots the team had or conceded

        if 'concede' in incoming_msg:
            result = df[df['AwayTeam'] == team[0]]['HS'].sum() + df[df['HomeTeam'] == team[0]]['AS'].sum()
            reply = f'{team[0].title()} conceded {result} shots.'

        else:
            result = df[df['HomeTeam'] == team[0]]['HS'].sum() + df[df['AwayTeam'] == team[0]]['AS'].sum()
            reply = f'{team[0].title()} had {result} shots.'

    elif len(team) == 2:
        # this question is about getting stats for a match

        result = df[(df['HomeTeam'] == team[0]) & (df['AwayTeam'] == team[1])].iloc[0]
        reply = (f"*{team[0].title()} {result['FTHG']} - {result['FTAG']} {team[1].title()}*\n"
                 f"Date: {result['Date']}\n"
                 f"Referee: {result['Referee']}\n"
                 f"Shots: {result['HS']} - {result['AS']}\n"
                 f"Corners: {result['HC']} - {result['AC']}\n"
                 f"Yellow cards: {result['HY']} - {result['AY']}\n"
                 f"Red cards: {result['HR']} - {result['AR']}")

    else:
        # prompt user to see example questions in case message is not understood
        reply = "I'm sorry but I don't understand your question.  You can see some example questions by typing in 'hello'."

    msg.body(reply)
    return str(resp)
