#!/usr/bin/env python3
"""
Author:  Lenar Gumerov  (tg: @lenargum)
"""

import logging
import requests
from requests.exceptions import HTTPError

from telegram_bot.secret import token, host_address

from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)
from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
    ParseMode
)
from telegram.error import (
    TelegramError,
    Unauthorized,
    BadRequest,
    TimedOut,
    ChatMigrated,
    NetworkError)

# Logging configuration
custom_format = "%(asctime)s - %(levelname)s - %(message)s"
formatter = logging.Formatter(custom_format)
logging.basicConfig(format=custom_format)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

QUESTION, ANSWER, OPERATOR = range(3)
CATEGORY_PROPERTY, REQUEST_PROPERTY, CLARIFICATION_PROPERTY, QUESTION_PROPERTY, ANSWER_PROPERTY, REVIEW = range(6)

BAD_ANSWER = "Ответ не подходит"
NEW_ANSWER = "Новый вопрос"
CALL_OPERATOR = "Позвать оператора"

OPERATOR_GREETING_STUB = '🙋‍♂️Здравствуйте! Меня зовут Петя. Я оператор\n\nПерезагружать пробовали?'


def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        '🤖Вас приветствует чат-бот для поиска ответов на ваши вопросы по нашему сервису!\n\n'
        'Отправьте интересующий вас вопрос',
        reply_markup=ReplyKeyboardRemove()
    )
    user = update.message.from_user
    drop_states(user.id)
    logger.info("%s %s started dialogue.", user.first_name, user.last_name)

    return QUESTION


def question(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    text = update.message.text

    logger.info("Question of %s: %s", user.first_name, text)

    if text[0] == '\"' and text[-1] == '\"':
        text = text[1:-1]

    if text == CALL_OPERATOR:
        try:
            response = requests.get(
                "{}/bot/v1/question/{}/operator".format(host_address, user.id)
            )
            response.raise_for_status()

            update.message.reply_text(
                "🤖Сейчас мы перенаправим вас на свободного оператора для более эффективной помощи.\n"
                "Пожалуйста, подождите\n\n"
                "/cancel - отменить",
                reply_markup=ReplyKeyboardRemove()
            )
            update.message.reply_text(
                OPERATOR_GREETING_STUB,
                reply_markup=ReplyKeyboardRemove()
            )

            return OPERATOR
        except HTTPError as http_err:
            logger.exception(f'HTTP error occurred: {http_err}')
        except Exception as err:
            logger.exception(f'Other error occurred: {err}')

    answer_type = ''
    answer_data = 'Что-то пошло не так...'
    answer_options = []

    try:
        response = requests.post(
            "{}/bot/v1/question/{}".format(host_address, user.id),
            json={
                "question": update.message.text
            })

        response.raise_for_status()
        json_response = response.json()

        answer_type = json_response['type']
        answer_data = json_response['answer']
        answer_options = json_response['options']
    except HTTPError as http_err:
        logger.exception(f'HTTP error occurred: {http_err}')
    except Exception as err:
        logger.exception(f'Other error occurred: {err}')

    return resolve_response(update, answer_data, answer_type, answer_options)


def answer(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    text = update.message.text
    logger.info("Answer of %s: %s", user.first_name, text)

    if text == NEW_ANSWER:
        return new_question(update, user.id)
    elif text == BAD_ANSWER:
        update.message.reply_text(
            "🤖У нас есть другой ответ, который возможно вам поможет:",
            reply_markup=ReplyKeyboardRemove()
        )

        answer_type = ''
        answer_data = 'Что-то пошло не так...'
        answer_options = []

        try:
            response = requests.get(
                "{}/bot/v1/question/{}/incorrect".format(host_address, user.id)
            )
            response.raise_for_status()
            json_response = response.json()

            answer_type = json_response['type']
            answer_data = json_response['answer']
            answer_options = json_response['options']
        except HTTPError as http_err:
            logger.exception(f'HTTP error occurred: {http_err}')
        except Exception as err:
            logger.exception(f'Other error occurred: {err}')

        return resolve_response(update, answer_data, answer_type, answer_options)

    return QUESTION


def questions_cancel(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    drop_states(user.id)
    update.message.reply_text(
        '🤖Начнем сначала!\n\n'
        'Отправьте интересующий вас вопрос', reply_markup=ReplyKeyboardRemove()
    )

    return QUESTION


def operator(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    text = update.message.text
    logger.info("Operator state achieved by %s", user.first_name)

    if text.lower() == 'да':
        update.message.reply_text(
            '🙋‍♂️Попробуйте перезагрузить компьютер 3 раза', reply_markup=ReplyKeyboardRemove()
        )
        return OPERATOR

    update.message.reply_text(
        '🙋‍♂️Перезагрузка не помогла, да?', reply_markup=ReplyKeyboardRemove()
    )
    return OPERATOR


def resolve_response(update: Update, answer_data: str, answer_type: str, answer_options: list) -> int:
    if answer_type == 'final':
        reply_keyboard = [[NEW_ANSWER, BAD_ANSWER]]
        update.message.reply_text(
            "🤖" + answer_data,
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
        )
        return ANSWER
    elif answer_type == 'clarification':
        reply_keyboard = [['\"' + item + '\"' for item in answer_options], [CALL_OPERATOR]]
        update.message.reply_text(
            "🤖" + answer_data,
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
        )
        return QUESTION
    elif answer_type == 'operator':
        update.message.reply_text(
            "🤖Сейчас мы перенаправим вас на свободного оператора для более эффективной помощи.\n"
            "Пожалуйста, подождите\n\n"
            "/cancel - отменить",
            reply_markup=ReplyKeyboardRemove()
        )
        update.message.reply_text(
            OPERATOR_GREETING_STUB,
            reply_markup=ReplyKeyboardRemove()
        )
        return OPERATOR
    else:
        update.message.reply_text(
            "🤖🤷Что-то пошло не так, когда бот пытался обратиться к базе знаний...\n"
            "Пожалуйста, повторите попытку позднее!",
            reply_markup=ReplyKeyboardRemove()
        )
        return QUESTION


def new_question(update: Update, user_id) -> int:
    update.message.reply_text(
        "🤖Ждем ваш новый вопрос!",
        reply_markup=ReplyKeyboardRemove()
    )
    drop_states(user_id)
    return QUESTION


def drop_states(chatid):
    try:
        response = requests.get(
            "{}/bot/v1/question/{}/cancel".format(host_address, chatid)
        )
        response.raise_for_status()
    except HTTPError as http_err:
        logger.exception(f'HTTP error occurred: {http_err}')
    except Exception as err:
        logger.exception(f'Other error occurred: {err}')


def error_callback(update, context):
    try:
        raise context.error
    except Unauthorized as e:
        logger.exception("Unauthorized: %s", str(e))
    except BadRequest as e:
        logger.exception("BadRequest: %s", str(e))
        # handle malformed requests - read more below!
    except TimedOut as e:
        logger.exception("TimedOut: %s", str(e))
        # handle slow connection problems
    except NetworkError as e:
        logger.exception("NetworkError: %s", str(e))
        # handle other connection problems
    except ChatMigrated as e:
        logger.exception("ChatMigrated: %s", str(e))
        # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError as e:
        logger.exception("TelegramError: %s", str(e))
        # handle all other telegram_bot related errors
    except Exception as e:
        logger.exception("Exception: %s", str(e))
        # handle all other errors


def addition_start(update: Update, context: CallbackContext) -> int:
    reply_keyboard = [["Телефон", "Телевидение", "Мобильная связь", "Интернет", "Видеонаблюдение"]]

    drop_userdata(context)
    update.message.reply_text(
        '🤖Чтобы добавить вопрос-ответ, нужно ввести:\n'
        '- Сферу обслуживания вопроса\n'
        '- Категорию вопроса\n'
        '- Подкатегорию вопроса\n'
        '- Сам вопрос\n'
        '- Ответ на вопрос\n\n'
        'Для начала вам нужно ввести cферу обслуживания вопроса.\n'
        'Выберите её из предложенных кнопок.\n\n'
        '<b>ВНИМАНИЕ!</b> Изменить эту часть позже нельзя',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
        parse_mode=ParseMode.HTML
    )
    user = update.message.from_user
    logger.info("%s %s want to add new question", user.first_name, user.last_name)

    return CATEGORY_PROPERTY


def addition_cancel(update: Update, context: CallbackContext) -> int:
    drop_userdata(context)
    update.message.reply_text(
        '🤖Процесс добавления нового вопроса отменен.\n\n'
        '/start - задать вопрос\n'
        '/add_question - добавить новый вопрос заново',
        reply_markup=ReplyKeyboardRemove()
    )
    user = update.message.from_user
    logger.info("%s %s canceled adding new question", user.first_name, user.last_name)
    return ConversationHandler.END


def addition_category(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    text = update.message.text
    logger.info("%s choosed %s category", user.first_name, text)

    context.user_data['category'] = text
    update.message.reply_text(
        '🤖Теперь введите категорию вопроса.\n\n'
        'Например, если сфера обслуживания была <b>Телефон</b>, то категорией является <b>Домашний телефон</b>.\n\n'
        'Если вы уже заполняли этот пункт и хотите оставить раннее внесенные данные, отправьте /skip',
        reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.HTML
    )

    return REQUEST_PROPERTY


def addition_request(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    text = update.message.text

    update.message.reply_text(
        '🤖Теперь введите подкатегорию вопроса.\n\n'
        'Например, если категория была <b>Домашний телефон</b>, то подкатегорией является <b>Подключение</b>.\n\n'
        'Если вы уже заполняли этот пункт и хотите оставить раннее внесенные данные, отправьте /skip',
        reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.HTML
    )

    if text == "/skip":
        return CLARIFICATION_PROPERTY

    context.user_data['request'] = text
    return CLARIFICATION_PROPERTY


def addition_clarification(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    text = update.message.text

    update.message.reply_text(
        '🤖Теперь введите сам вопрос.\n\n'
        'Если вы уже заполняли этот пункт и хотите оставить раннее внесенные данные, отправьте /skip',
        reply_markup=ReplyKeyboardRemove()
    )

    if text == "/skip":
        return QUESTION_PROPERTY

    context.user_data['clarification'] = text
    return QUESTION_PROPERTY


def addition_question(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    text = update.message.text

    update.message.reply_text(
        '🤖Теперь введите ответ на вопрос.\n\n'
        'Если вы уже заполняли этот пункт и хотите оставить раннее внесенные данные, отправьте /skip',
        reply_markup=ReplyKeyboardRemove()
    )

    if text == "/skip":
        return ANSWER_PROPERTY

    context.user_data['question'] = text
    return ANSWER_PROPERTY


def addition_answer(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    text = update.message.text

    if text != "/skip":
        context.user_data['answer'] = text

    category = "❌" if 'category' not in context.user_data else context.user_data['category']
    category = category.strip()
    request = "❌" if 'request' not in context.user_data else context.user_data['request']
    request = request.strip()
    clarification = "❌" if 'clarification' not in context.user_data else context.user_data['clarification']
    clarification = clarification.strip()
    question_temp = "❌" if 'question' not in context.user_data else context.user_data['question']
    question_temp = question_temp.strip()
    answer_temp = "❌" if 'answer' not in context.user_data else context.user_data['answer']
    answer_temp = answer_temp.strip()

    reply_keyboard = [["Категория вопроса", "Подкатегория вопроса", "Вопрос", "Ответ"],
                      ["Завершить"]]

    update.message.reply_text(
        '🤖Ваши введенные данные: '
        '\n<b>Сфера обслуживания вопроса:</b> ' + category +
        '\n<b>Категория вопроса:</b> ' + request +
        '\n<b>Подкатегория вопроса:</b> ' + clarification +
        '\n<b>Вопрос:</b> ' + question_temp +
        '\n<b>Ответ:</b> ' + answer_temp + "\n\n"
                                           "Все поля кроме <i>подкатегории вопроса</i> должны быть заполнены.\n"
                                           "Желаете что-то изменить или завершить добавление вопроса-ответа?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
        parse_mode=ParseMode.HTML
    )

    return REVIEW


def addition_review(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    text = update.message.text

    if text == "Категория вопроса":
        update.message.reply_text("🤖Отправьте /skip и введите её.",
                                  reply_markup=ReplyKeyboardRemove())
        return CATEGORY_PROPERTY
    elif text == "Подкатегория вопроса":
        update.message.reply_text("🤖Отправьте /skip и введите её.",
                                  reply_markup=ReplyKeyboardRemove())
        return REQUEST_PROPERTY
    elif text == "Вопрос":
        update.message.reply_text("🤖Отправьте /skip и введите его.",
                                  reply_markup=ReplyKeyboardRemove())
        return CLARIFICATION_PROPERTY
    elif text == "Ответ":
        update.message.reply_text("🤖Отправьте /skip и введите его.",
                                  reply_markup=ReplyKeyboardRemove())
        return QUESTION_PROPERTY
    elif text == "Завершить":
        category = context.user_data['category'].strip()
        request = None if 'request' not in context.user_data else context.user_data['request'].strip()
        if request is None:
            update.message.reply_text("🤖Категория должна быть введена.\n"
                                      "Отправьте /skip и введите её.",
                                      reply_markup=ReplyKeyboardRemove())
            return CATEGORY_PROPERTY
        clarification = None if 'clarification' not in context.user_data else context.user_data['clarification'].strip()
        if clarification is None:
            clarification = "Нет"
        question_temp = None if 'question' not in context.user_data else context.user_data['question'].strip()
        if question_temp is None:
            update.message.reply_text("🤖Вопрос должен быть введен.\n"
                                      "Отправьте /skip и введите его.",
                                      reply_markup=ReplyKeyboardRemove())
            return CLARIFICATION_PROPERTY
        answer_temp = None if 'answer' not in context.user_data else context.user_data['answer'].strip()
        if answer_temp is None:
            update.message.reply_text("🤖Ответ должен быть введен.\n"
                                      "Отправьте /skip и введите его.",
                                      reply_markup=ReplyKeyboardRemove())
            return QUESTION_PROPERTY

        try:
            response = requests.post(
                "{}/bot/v1/index/new".format(host_address),
                json={
                    "category": category,
                    "request": request,
                    "clarification": clarification,
                    "question": question_temp,
                    "answer": answer_temp
                })
            response.raise_for_status()
            logger.info(
                "%s added question: category=(%s), request=(%s), clarification=(%s), question=(%s), answer=(%s)",
                user.first_name, category, request, clarification, question_temp, answer_temp)
            update.message.reply_text("🤖Вопрос-ответ добавлен успешно! \n\n"
                                      "/start - Задать новый вопрос\n"
                                      "/add_question - Добавить новый вопрос-ответ",
                                      reply_markup=ReplyKeyboardRemove())
        except HTTPError as http_err:
            logger.exception(f'HTTP error occurred: {http_err}')
        except Exception as err:
            logger.exception(f'Other error occurred: {err}')


def drop_userdata(context: CallbackContext):
    if 'category' in context.user_data:
        del context.user_data['category']
    if 'request' in context.user_data:
        del context.user_data['request']
    if 'clarification' in context.user_data:
        del context.user_data['clarification']
    if 'question' in context.user_data:
        del context.user_data['question']
    if 'answer' in context.user_data:
        del context.user_data['answer']


def main() -> None:
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(token=token, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    questions_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            QUESTION: [CommandHandler('cancel', questions_cancel), MessageHandler(Filters.text, question)],
            ANSWER: [CommandHandler('cancel', questions_cancel), MessageHandler(Filters.text, answer)],
            OPERATOR: [CommandHandler('cancel', questions_cancel), MessageHandler(Filters.text, operator)]
        },
        fallbacks=[CommandHandler('cancel', questions_cancel)],
        allow_reentry=True
    )

    # NEW_QUESTION, CATEGORY_PROPERTY, REQUEST_PROPERTY, CLARIFICATION_PROPERTY, QUESTION_PROPERTY, ANSWER_PROPERTY, REVIEW
    new_question_handler = ConversationHandler(
        entry_points=[CommandHandler('add_question', addition_start)],
        states={
            CATEGORY_PROPERTY: [CommandHandler('addition_cancel', questions_cancel),
                                MessageHandler(Filters.text, addition_category)],
            REQUEST_PROPERTY: [CommandHandler('addition_cancel', questions_cancel),
                               MessageHandler(Filters.text, addition_request)],
            CLARIFICATION_PROPERTY: [CommandHandler('addition_cancel', questions_cancel),
                                     MessageHandler(Filters.text, addition_clarification)],
            QUESTION_PROPERTY: [CommandHandler('addition_cancel', questions_cancel),
                                MessageHandler(Filters.text, addition_question)],
            ANSWER_PROPERTY: [CommandHandler('addition_cancel', questions_cancel),
                              MessageHandler(Filters.text, addition_answer)],
            REVIEW: [CommandHandler('addition_cancel', questions_cancel), MessageHandler(Filters.text, addition_review)]
        },
        fallbacks=[CommandHandler('addition_cancel', addition_cancel)],
        allow_reentry=True
    )

    dispatcher.add_handler(questions_handler)
    dispatcher.add_handler(new_question_handler)
    dispatcher.add_error_handler(error_callback)

    logger.info("Bot initialized")
    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
