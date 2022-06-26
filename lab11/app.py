from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, session, url_for, redirect, request, flash
from flask_sqlalchemy import SQLAlchemy

# Оголошення фласк-програми та налаштування конфігурації
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///okean_elzy.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)


class Album(db.Model):
    """
    Клас, який буде використаний як таблиця (ORM) в БД okean_elzy.db для зберігання альбомів
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(200), nullable=False)
    year = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return '<Album %r>' % self.id


class Users(db.Model):
    """
    Клас, який буде використаний як таблиця (ORM) в БД okean_elzy.db для зберігання альбомів
    """
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f"<users {self.id}>"


"""
@albums

Без меж             /2016
Земля               /2013
Dolce Vita          /2010
Міра                /2007
Gloria              /2005
Суперсиметрія       /2003
Модель              /2001
Янанебібув          /2000
Там, де нас нема    /1998
"""


@app.route('/')
@app.route('/home')
# Візуалізуємо головну сторінку, за допомогою render_template
def index():
    return render_template('index.html')


@app.route('/about')
# Візуалізуємо сторінку "Про проект"
def about():
    return render_template('about.html')


@app.route('/album')
def album():
    # ДІСТАЄМО З БД АЛЬБОМИ та сортумо за роками випуску
    albums = db.session.query(Album).order_by(Album.year.desc()).all()
    return render_template('album.html', albums=albums)


@app.route('/history')
# Візуалізуємо сторінку з історією гурту
def history():
    return render_template('history.html')


@app.route('/login', methods=["POST", "GET"])
# Входження користувача у свій акаунт
def login():
    # POST:
    if request.method == 'POST':
        # Якщо пошта та пароль підходять за умовою то записуємо їх в окремі змінні
        if len(request.form['email']) > 0 and len(request.form['password']) >= 3:
            email = request.form['email']
            psw = request.form['password']

            # Далі виконуємо діставання з БД запису з відповідною поштою, за допомогою ORM,
            # що еквівалентно SELECT * FROM Users WHERE email = email
            user = Users.query.filter_by(email=email).first()

            # Якщо юзер є в БД, то перевіряємо хеш його паролю записуємо в сесію пошту та перекидаємо на головну
            if user is not None:
                if check_password_hash(pwhash=user.password, password=psw):
                    session['user'] = email
                    return redirect('/home')
            # Інакше користувач залишається на цій сторінці
            else:
                redirect('/login')
        else:
            return render_template('login.html')
    # GET:
    return render_template('login.html')


@app.route('/exit')
# Функція для виходу користувача зі свого акаунту. Видаляємо його з сесії
def exit():
    session.pop('user', None)
    return redirect('/login')


@app.route('/register', methods=['GET', 'POST'])
# Функція для реєстрації користувачів
def sign_up():
    # POST:
    if request.method == 'POST':
        try:
            # Хешуємо введений користувачем пароль
            hash = generate_password_hash(request.form['password'])

            # Якщо обидва паролі НЕ співпадають і довжина менша за 3 то перериваємо реєстрацію
            if request.form['password'] != request.form['password_confirm'] and len(request.form['password']) < 3:
                return redirect('/register')

            # Якщо все ОК з віхдними даними, то створюємо об'єкт класу User та додаємо дані у таблицю в базі даних
            u = Users(email=request.form['login'], password=hash)
            db.session.add(u)
            db.session.commit()
            return redirect('/login')
        except:
            # Якщо щось піде не так, то скасовуємо зміни
            db.session.rollback()
            return "Не вдалось вставити користувача до БД."
    # GET:
    return render_template('signup.html')


# Імпорт бібліотек для наступної роботи при завантаженні зображень з форми у папку проекту
import os
from werkzeug.utils import secure_filename

# Папка, куди будуть збережені світлини
UPLOAD_FOLDER = 'static/uploads'
# Всі можливі роширення
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Додаємо конфіг та секретний ключ для безпеки
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = '1111'


# Функція, яка перевіряє чи підходить по формату завантажене зображення
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/album_create', methods=['GET', 'POST'])
# Функція для створення альбому
def album_create():
    # POST:
    if request.method == 'POST':
        try:
            # Перевірка на те, чи є у запиті файл
            if 'file' not in request.files:
                flash('Немає шляху до файлу')
                return redirect(request.url)
            file = request.files['file']

            if file.filename == '':
                flash('Файл не обрано')
                return redirect(request.url)

            # Якщо все ОК, то зберігаємо файл у папку uploads у нашому проекті
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                # Записуємо в окремі змінні назву та рік альбому
                album_title = request.form['album_title']
                album_year = request.form['album_year']

                # Створюємо об'єкт альбому, та аналогічно з User, через ORM додаємо запис в базу,
                # де image - назва картинка, до якої ми будемо звертатись уже в HTML,
                # прописуючи шлях static/uploads/image
                a = Album(year=album_year, title=album_title, image=filename)
                db.session.add(a)
                db.session.commit()

                # Переходимо до сторінки з альбомами
                return redirect(url_for('album'))
        except:
            db.session.rollback()
    # GET:
    return render_template('album_create.html')


@app.route('/album_update/<int:id>', methods=['GET', 'POST'])
# Функція для оновлення альбому
def album_update(id):
    # Дістаємо з БД потрібний запис та утворюємо відповідний об'єкт
    album = Album.query.get(id)

    # POST:
    if request.method == 'POST':
        try:
            file = ''

            # Якщо файл завантажено то зчитуємо його
            if 'file' in request.files:
                file = request.files['file']

            # Записуємо в окремі змінні назву та рік альбому
            album_title = request.form['album_title']
            album_year = request.form['album_year']

            # Якщо картинка правильна за розширенням та вона є
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                # Робимо оновлення запису РАЗОМ З КАРТИНКОЮ
                db.session.query(Album).filter(Album.id == id).update(
                    {Album.title: album_title, Album.year: album_year, Album.image: filename})

            # Робимо оновлення запису БЕЗ КАРТИНКИ, лишається поточна
            else:
                db.session.query(Album).filter(Album.id == id).update(
                    {Album.title: album_title, Album.year: album_year})

            # Комітимо зміни
            db.session.commit()
            return redirect(url_for('album'))
        except:
            # Якщо якась помилка, то відкатуємо назад і відміняємо коміт
            db.session.rollback()

    # GET:
    return render_template('album_update.html', album=album)


@app.route('/album_delete/<int:id>')
# Видалення альбому
def album_delete(id):
    # Дістаємо по ID альбом та видаляємо його
    db.session.query(Album).filter(Album.id == id).delete()
    db.session.commit()
    # Перенаправляємось на сторінку з альбомами
    return redirect('/album')


if __name__ == '__main__':
    app.run(debug=False)
