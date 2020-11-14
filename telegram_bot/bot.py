#!/usr/bin/env python3
"""
Author: Lenar Gumerov (tg: @lenargum)
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
    Update
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


def cancel(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
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
            "🤖"+answer_data,
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
        )
        return ANSWER
    elif answer_type == 'clarification':
        reply_keyboard = [['\"' + item + '\"' for item in answer_options], [CALL_OPERATOR]]
        update.message.reply_text(
            "🤖"+answer_data,
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

    try:
        response = requests.get(
            "{}/bot/v1/question/{}/cancel".format(host_address, user_id)
        )
        response.raise_for_status()
    except HTTPError as http_err:
        logger.exception(f'HTTP error occurred: {http_err}')
    except Exception as err:
        logger.exception(f'Other error occurred: {err}')
    return QUESTION


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


def main() -> None:
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(token=token, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            QUESTION: [CommandHandler('cancel', cancel), MessageHandler(Filters.text, question)],
            ANSWER: [CommandHandler('cancel', cancel), MessageHandler(Filters.text, answer)],
            OPERATOR: [CommandHandler('cancel', cancel), MessageHandler(Filters.text, operator)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )

    dispatcher.add_handler(conv_handler)
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
