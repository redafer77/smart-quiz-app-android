from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
import os

APP_STORAGE_FILE = "questions.txt"


class AndroidQuizApp(App):
    def build(self):
        self.title = "تطبيق الاختبارات الذكي"
        self.questions = []
        self.current_index = 0
        self.score = 0
        self.timer_seconds = 600
        self.timer_event = None
        self.selected_answer = None

        self.main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)

        self._build_home_screen()
        self._build_add_screen()
        self._build_quiz_screen()
        self._build_result_screen()

        self.main_layout.add_widget(self.home_layout)
        return self.main_layout

    def _clear_and_show(self, layout):
        self.main_layout.clear_widgets()
        self.main_layout.add_widget(layout)

    def _build_home_screen(self):
        self.home_layout = BoxLayout(orientation='vertical', spacing=15)

        self.welcome_label = Label(
            text="مرحباً بك في تطبيق الاختبارات والمؤقتات",
            font_size='20sp', size_hint_y=None, height=60,
            halign='center', valign='middle'
        )
        self.welcome_label.bind(size=lambda *a: setattr(self.welcome_label, 'text_size', self.welcome_label.size))
        self.home_layout.add_widget(self.welcome_label)

        self.status_label = Label(text="", font_size='16sp', size_hint_y=None, height=30)
        self.home_layout.add_widget(self.status_label)

        btn_add_screen = Button(text="➕ إضافة أسئلة جديدة", font_size='18sp',
                                 background_color=(0.2, 0.6, 0.8, 1), size_hint_y=None, height=55)
        btn_add_screen.bind(on_press=self.show_add_question_screen)
        self.home_layout.add_widget(btn_add_screen)

        btn_load_file = Button(text="📂 تحميل الأسئلة من ملف جاهز", font_size='18sp',
                                background_color=(0.1, 0.6, 0.3, 1), size_hint_y=None, height=55)
        btn_load_file.bind(on_press=self.load_default_file)
        self.home_layout.add_widget(btn_load_file)

        btn_start_quiz = Button(text="🚀 بدء الاختبار", font_size='18sp',
                                 background_color=(0.8, 0.5, 0.1, 1), size_hint_y=None, height=55)
        btn_start_quiz.bind(on_press=self.start_quiz)
        self.home_layout.add_widget(btn_start_quiz)

        self.home_layout.add_widget(BoxLayout())

    def _build_add_screen(self):
        self.add_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        self.add_layout.add_widget(Label(text="إضافة سؤال جديد إلى الملف", font_size='18sp',
                                          size_hint_y=None, height=40))

        self.input_q = TextInput(hint_text="اكتب السؤال هنا...", font_size='16sp',
                                  size_hint_y=None, height=45, multiline=False)
        self.add_layout.add_widget(self.input_q)

        self.input_opt1 = TextInput(hint_text="الخيار أ) مثلاً", font_size='16sp',
                                     size_hint_y=None, height=40, multiline=False)
        self.add_layout.add_widget(self.input_opt1)

        self.input_opt2 = TextInput(hint_text="الخيار ب) مثلاً", font_size='16sp',
                                     size_hint_y=None, height=40, multiline=False)
        self.add_layout.add_widget(self.input_opt2)

        self.input_opt3 = TextInput(hint_text="الخيار ج) مثلاً (اختياري)", font_size='16sp',
                                     size_hint_y=None, height=40, multiline=False)
        self.add_layout.add_widget(self.input_opt3)

        self.input_opt4 = TextInput(hint_text="الخيار د) مثلاً (اختياري)", font_size='16sp',
                                     size_hint_y=None, height=40, multiline=False)
        self.add_layout.add_widget(self.input_opt4)

        self.input_ans = TextInput(hint_text="الإجابة الصحيحة (مثل: أ)", font_size='16sp',
                                    size_hint_y=None, height=40, multiline=False)
        self.add_layout.add_widget(self.input_ans)

        btn_save_q = Button(text="💾 حفظ السؤال في ملف التخزين", font_size='16sp',
                             background_color=(0.8, 0.4, 0.1, 1), size_hint_y=None, height=48)
        btn_save_q.bind(on_press=self.save_new_question)
        self.add_layout.add_widget(btn_save_q)

        btn_back_home = Button(text="⬅️ العودة للقائمة الرئيسية", font_size='16sp',
                                background_color=(0.5, 0.5, 0.5, 1), size_hint_y=None, height=48)
        btn_back_home.bind(on_press=self.back_to_home)
        self.add_layout.add_widget(btn_back_home)

        self.add_layout.add_widget(BoxLayout())

    def _build_quiz_screen(self):
        self.quiz_layout = BoxLayout(orientation='vertical', spacing=12, padding=10)

        top_row = BoxLayout(size_hint_y=None, height=40)
        self.timer_label = Label(text="⏱️ 10:00", font_size='18sp')
        self.progress_label = Label(text="السؤال 1 / 1", font_size='16sp')
        top_row.add_widget(self.timer_label)
        top_row.add_widget(self.progress_label)
        self.quiz_layout.add_widget(top_row)

        self.question_label = Label(text="", font_size='20sp', size_hint_y=None, height=100,
                                     halign='center', valign='middle')
        self.question_label.bind(size=lambda *a: setattr(self.question_label, 'text_size', self.question_label.size))
        self.quiz_layout.add_widget(self.question_label)

        self.options_box = BoxLayout(orientation='vertical', spacing=8, size_hint_y=None)
        self.options_box.bind(minimum_height=self.options_box.setter('height'))
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(self.options_box)
        self.quiz_layout.add_widget(scroll)

        nav_row = BoxLayout(size_hint_y=None, height=50, spacing=10)
        self.btn_next = Button(text="التالي ➡️", background_color=(0.2, 0.6, 0.8, 1))
        self.btn_next.bind(on_press=self.next_question)
        btn_quit = Button(text="⛔ إنهاء الاختبار", background_color=(0.7, 0.2, 0.2, 1))
        btn_quit.bind(on_press=self.end_quiz)
        nav_row.add_widget(self.btn_next)
        nav_row.add_widget(btn_quit)
        self.quiz_layout.add_widget(nav_row)

    def _build_result_screen(self):
        self.result_layout = BoxLayout(orientation='vertical', spacing=15, padding=20)
        self.result_label = Label(text="", font_size='22sp', halign='center', valign='middle')
        self.result_label.bind(size=lambda *a: setattr(self.result_label, 'text_size', self.result_label.size))
        self.result_layout.add_widget(self.result_label)

        btn_retry = Button(text="🔁 إعادة الاختبار", size_hint_y=None, height=50,
                            background_color=(0.2, 0.6, 0.8, 1))
        btn_retry.bind(on_press=self.start_quiz)
        self.result_layout.add_widget(btn_retry)

        btn_home = Button(text="🏠 القائمة الرئيسية", size_hint_y=None, height=50,
                           background_color=(0.5, 0.5, 0.5, 1))
        btn_home.bind(on_press=self.back_to_home)
        self.result_layout.add_widget(btn_home)

    def show_add_question_screen(self, instance):
        self._clear_and_show(self.add_layout)

    def back_to_home(self, instance):
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None
        self._clear_and_show(self.home_layout)

    def save_new_question(self, instance):
        q_text = self.input_q.text.strip()
        o1 = self.input_opt1.text.strip()
        o2 = self.input_opt2.text.strip()
        o3 = self.input_opt3.text.strip()
        o4 = self.input_opt4.text.strip()
        ans = self.input_ans.text.strip()

        if not q_text or not o1 or not o2 or not ans:
            self.status_label.text = "⚠️ الرجاء تعبئة السؤال وخيارين على الأقل والإجابة!"
            self._clear_and_show(self.home_layout)
            return

        block = f"سؤال: {q_text}\nأ) {o1}\nب) {o2}\n"
        if o3:
            block += f"ج) {o3}\n"
        if o4:
            block += f"د) {o4}\n"
        block += f"الإجابة: {ans}\n\n"

        try:
            path = self._get_storage_path()
            with open(path, "a", encoding="utf-8") as f:
                f.write(block)
            self.status_label.text = "✅ تم إضافة وحفظ السؤال بنجاح!"
            self.input_q.text = ""
            self.input_opt1.text = ""
            self.input_opt2.text = ""
            self.input_opt3.text = ""
            self.input_opt4.text = ""
            self.input_ans.text = ""
            self.back_to_home(None)
        except Exception as e:
            self.status_label.text = f"❌ خطأ في الحفظ: {e}"

    def _get_storage_path(self):
        try:
            from android.storage import app_storage_path
            base = app_storage_path()
        except Exception:
            base = os.getcwd()
        return os.path.join(base, APP_STORAGE_FILE)

    def load_default_file(self, instance):
        path = self._get_storage_path()
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write("سؤال: ما عاصمة المغرب؟\nأ) مراكش\nب) الرباط\nج) الدار البيضاء\nالإجابة: ب\n\n")

        try:
            with open(path, "r", encoding="utf-8") as file:
                content = file.read().strip().split("\n\n")
                self.questions = []
                for block in content:
                    lines = [l for l in block.split("\n") if l.strip()]
                    q_data = {"question": "", "options": [], "answer": ""}
                    for line in lines:
                        if line.startswith("سؤال:"):
                            q_data["question"] = line.replace("سؤال:", "").strip()
                        elif line[:2] in ("أ)", "ب)", "ج)", "د)"):
                            q_data["options"].append(line.strip())
                        elif line.startswith("الإجابة:"):
                            q_data["answer"] = line.replace("الإجابة:", "").strip()
                    if q_data["question"] and q_data["options"]:
                        self.questions.append(q_data)

            if self.questions:
                self.status_label.text = f"✅ تم تحميل {len(self.questions)} سؤال بنجاح! جاهز للبدء."
            else:
                self.status_label.text = "⚠️ الملف فارغ أو لا يحتوي على أسئلة مطابقة."
        except Exception as e:
            self.status_label.text = f"❌ خطأ في القراءة: {e}"

    def start_quiz(self, instance):
        if not self.questions:
            self.load_default_file(None)
        if not self.questions:
            self.status_label.text = "⚠️ لا توجد أسئلة. أضف أسئلة أولاً."
            self._clear_and_show(self.home_layout)
            return

        self.current_index = 0
        self.score = 0
        self.timer_seconds = 600
        self._show_question()
        self._clear_and_show(self.quiz_layout)

        if self.timer_event:
            self.timer_event.cancel()
        self.timer_event = Clock.schedule_interval(self._tick_timer, 1)

    def _tick_timer(self, dt):
        self.timer_seconds -= 1
        minutes, seconds = divmod(max(self.timer_seconds, 0), 60)
        self.timer_label.text = f"⏱️ {minutes:02d}:{seconds:02d}"
        if self.timer_seconds <= 0:
            self.timer_event.cancel()
            self.timer_event = None
            self.end_quiz(None)

    def _show_question(self):
        q = self.questions[self.current_index]
        self.progress_label.text = f"السؤال {self.current_index + 1} / {len(self.questions)}"
        self.question_label.text = q["question"]
        self.selected_answer = None

        self.options_box.clear_widgets()
        for opt in q["options"]:
            btn = Button(text=opt, size_hint_y=None, height=48,
                         background_color=(0.9, 0.9, 0.9, 1), color=(0, 0, 0, 1))
            btn.bind(on_press=self._select_option)
            self.options_box.add_widget(btn)

    def _select_option(self, instance):
        letter = instance.text[0]
        self.selected_answer = letter
        for child in self.options_box.children:
            if child.text[0] == letter:
                child.background_color = (0.3, 0.7, 0.9, 1)
            else:
                child.background_color = (0.9, 0.9, 0.9, 1)

    def next_question(self, instance):
        q = self.questions[self.current_index]
        if self.selected_answer and self.selected_answer == q["answer"]:
            self.score += 1

        if self.current_index + 1 < len(self.questions):
            self.current_index += 1
            self._show_question()
        else:
            self.end_quiz(None)

    def end_quiz(self, instance):
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None
        total = len(self.questions) if self.questions else 1
        self.result_label.text = (
            f"🎉 انتهى الاختبار!\n\nنتيجتك: {self.score} من {total}\n"
            f"النسبة: {round((self.score / total) * 100, 1)}%"
        )
        self._clear_and_show(self.result_layout)


if __name__ == '__main__':
    AndroidQuizApp().run()
