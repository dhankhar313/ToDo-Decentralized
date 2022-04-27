from flask import *
import mysql.connector
import os

app = Flask(__name__)
dataBase = mysql.connector.connect(
    host="192.168.1.8",
    user="root",
    passwd=os.environ.get('mySQLPass')
)

cursor = dataBase.cursor()
cursor.execute('CREATE DATABASE IF NOT EXISTS TODOApp')
cursor.execute('USE TODOApp')
listsTable = "CREATE TABLE IF NOT EXISTS lists (title varchar(50),description varchar(400));"
tasksTable = "CREATE TABLE IF NOT EXISTS tasks (id int primary key auto_increment, description " \
             "varchar(400), status enum('0', '1'));"
hashtagTable = "CREATE TABLE IF NOT EXISTS hashtags (TaskID int, hashtag varchar(40), FOREIGN KEY (TaskID) REFERENCES" \
               " tasks(id));"
cursor.execute(listsTable)
cursor.execute(tasksTable)
cursor.execute(hashtagTable)

cursor.execute(f"SELECT * FROM lists;")
d1 = cursor.fetchall()
dataDict = {}
for i in d1:
    if dataDict.get(i[0], 0) == 0:
        dataDict[i[0]] = [i[1]]
    else:
        dataDict[i[0]].append(i[1])
titles = list(dataDict.keys())
items = [dataDict[i] for i in titles]


@app.route('/')
def home():
    return render_template('ht.html')


@app.route('/List', methods=['GET', 'POST'])
def lists():
    if request.method == 'POST':
        return render_template('lists.html', data=dataDict)

    else:
        return render_template('lists.html', data=dataDict)


def deleteList(title):
    cursor.execute(f"DELETE FROM lists WHERE title='{title}'")
    dataBase.commit()


@app.route('/delete/<string:title>')
def delete(title):
    del dataDict[title]
    deleteList(title)
    return redirect(url_for('lists'))


@app.route('/deleteitem/<string:title>/<string:item>')
def deleteitem(title, item):
    print('item: ', item)
    print('data: ', dataDict[title])
    flag = 0
    try:
        dataDict[title].remove(item)
    except:
        dataDict[title].remove(item + '\r')
        flag = 1
    if flag == 1:
        item = item + '\r'
        cursor.execute(f"DELETE FROM lists WHERE title='{title}' and description='{item}';")
    else:
        cursor.execute(f"DELETE FROM lists WHERE title='{title}' and description='{item}';")
    dataBase.commit()
    return redirect(url_for('lists'))


@app.route('/edit/<string:title>', methods=['GET', 'POST'])
def edit(title):
    if request.method == 'POST':
        del dataDict[title]
        deleteList(title)
        title = request.form['listtitle']
        updatedInfo = request.form['edititems'].split('\n')
        updatedInfo = [i for i in updatedInfo if i not in ['', '\r']]
        dataDict[title] = updatedInfo
        dataDict[title] = updatedInfo
        for i in updatedInfo:
            cursor.execute(f"INSERT lists VALUES ('{title}', '{i}')")
        dataBase.commit()
        return redirect(url_for('lists'))
    else:
        temp = ""
        for i in dataDict[title]:
            temp += i + "\n"
        return render_template('lists.html', title=title, items=temp, edit=True, data=dataDict)


@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        title = request.form['listtitle']
        items = request.form['items']
        data = [i.strip() for i in items.split('\n') if i not in ['', '\r']]
        dataDict[title] = data
        for i in data:
            cursor.execute(f"INSERT lists VALUES ('{title}', '{i}')")
        dataBase.commit()
        return redirect(url_for('lists'))


# ---------------------------------------------------------------------------------


cursor.execute(f"SELECT id, description FROM tasks where status='{0}';")
incomplete_tasks = cursor.fetchall()
cursor.execute(f"SELECT id, description FROM tasks where status='{1}';")
complete_tasks = cursor.fetchall()
incomplete_tasks = [item.replace('(', '').replace(')', '') for sublist in incomplete_tasks for item in sublist]
complete_tasks = [item.replace('(', '').replace(')', '') for sublist in complete_tasks for item in sublist]


@app.route('/Task')
def tasks():
    return render_template('tasks.html', data=incomplete_tasks + complete_tasks)


def getHashTags(desc):
    tags = []
    for i in desc.split():
        if i.startswith('#'):
            tags.append(i)
    return tags


def insertHashtags(desc, tags):
    if len(tags) == 0:
        cursor.execute(f"INSERT INTO hashtags VALUES ((SELECT id FROM tasks where description='{desc}'),'Undefined')")
    elif len(tags) == 1:
        cursor.execute(f"INSERT INTO hashtags VALUES ((SELECT id FROM tasks where description='{desc}'),'{tags[0]}')")
    else:
        for i in tags:
            cursor.execute(f"INSERT INTO hashtags VALUES ((SELECT id FROM tasks where description='{desc}'),'{i}')")
    dataBase.commit()


@app.route('/addTask', methods=['GET', 'POST'])
def addTask():
    if request.method == 'POST':
        title = '🔴' + " " + request.form['Tasktitle']
        incomplete_tasks.append(title)
        cursor.execute(f"INSERT INTO tasks(description, status) VALUES ('{title}', '0');")
        dataBase.commit()
        insertHashtags(title, getHashTags(title))
    return render_template('tasks.html', data=incomplete_tasks + complete_tasks)


@app.route('/editTask/<string:title>', methods=['GET', 'POST'])
def editTask(title):
    temp = title
    if request.method == 'POST':
        title = request.form['Tasktitle']
        print('Hello: ', title)
        incomplete_tasks.append('🔴' + " " + title)
        return redirect(url_for('addTask'))

    else:
        title = title.replace('🔴', '')

        return render_template('tasks.html', title=title, edit=True, data=incomplete_tasks + complete_tasks)


@app.route('/changestat/<string:title>', methods=['GET', 'POST'])
def changestat(title):
    print('Received title: ', title)
    if title.split()[0] == '🔴':
        incomplete_tasks.remove(title)
        cursor.execute(f"UPDATE tasks SET status='{1}' where description='{title}'")
        new_title = '🟢' + " " + title.split()[1]
        cursor.execute(f"UPDATE tasks SET description='{new_title}' where description='{title}'")
        complete_tasks.append(new_title)
    else:
        complete_tasks.remove(title)
        cursor.execute(f"UPDATE tasks SET status='{0}' where description='{title}'")
        new_title = '🔴' + " " + title.split()[1]
        cursor.execute(f"UPDATE tasks SET description='{new_title}' where description='{title}'")
        incomplete_tasks.append(title)
    dataBase.commit()
    return redirect(url_for('tasks'))


@app.route('/deleteTask/<string:title>')
def deleteTask(title):
    cursor.execute("DELETE FROM hashtags where TaskID='{SELECT id from tasks where description='{title}'}';")
    cursor.execute("DELETE FROM tasks where description='{title}';")
    dataBase.commit()

    return redirect(url_for('tasks'))


if __name__ == '__main__':
    app.run(debug=True)
