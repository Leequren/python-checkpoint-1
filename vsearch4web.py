import mysql.connector.errors
from flask import Flask, render_template, request, session, copy_current_request_context
from vsearch import search4letters
from threading import Thread
from DBcm import UseDatabase, ConnectionError, CredentialsError, SQLError
from checker import check_logged_in

app = Flask(__name__)
dbconfig = {'host': 'leequren.mysql.pythonanywhere-services.com',
            'user': 'leequren',
            'password': 'Ellyonor',
            'database': 'vsearchlogDB',
}


@app.route('/login')
def do_login() -> str:
    session['logged_in'] = True
    return 'You are now logged in.'


@app.route('/logout')
def do_logout() -> str:
    session.pop('logged_in')
    return 'You are now logged out.'


@app.route('/search4', methods=['POST'])
def do_search() -> 'html':
    @copy_current_request_context
    def log_request(req: 'flask_request', res: str) -> None:
        with UseDatabase(dbconfig) as cursor:
            reqSQL = '''insert into log (phrase, letters, ip, browser_string, results) values (%s, %s, %s, %s, %s)'''
            cursor.execute(reqSQL, (req.form['phrase'],
                                    req.form['letters'],
                                    req.remote_addr,
                                    str(req.user_agent),
                                    res,))

    phrase = request.form['phrase']
    letters = request.form['letters']
    title = 'Here are your results:'
    results = str(search4letters(phrase, letters))
    try:
        thread = Thread(target=log_request, args=(request, results))
        thread.start()
    except Exception as err:
        print('***** Logging failed with error: ', str(err))
    return render_template('results.html',
                           the_title=title,
                           the_phrase=phrase,
                           the_letters=letters,
                           the_results=results, )


@app.route('/')
@app.route('/entry')
def entry_page() -> 'html':
    return render_template('entry.html', the_title='Welcome')


@app.route('/viewlog')
@check_logged_in
def view_the_log() -> 'html':
    try:
        with UseDatabase(dbconfig) as cursor:
            reqSQL = '''select phrase, letters, ip, browser_string, results from log'''
            cursor.execute(reqSQL)
            contents = cursor.fetchall()
        titles = ('Phrase', 'Letters', 'Remote_addr', 'User_agent', 'Results')
        return render_template('viewlog.html',
                               the_title='View Log',
                               the_row_titles=titles,
                               the_data=contents, )
    except ConnectionError as err:
        print('Is your database switched on? Error: ', str(err))
    except CredentialsError as err:
        print('User-id/Password issues. Error: ', str(err))
    except SQLError as err:
        print('Is your query correct? Error: ', str(err))
    except Exception as err:
        print('Something went wrong: ', str(err))
    return 'Error'


app.secret_key = 'MyNameIsLeequrenLiquliphy'

if __name__ == '__main__':
    app.run(debug=True)
