# -*- coding: UTF-8 -*-

import asyncio
import json
import logging
import time

import mysql.connector
import requests
import telegram
from apscheduler.schedulers.background import BackgroundScheduler
from pysolusvm import SolusVM
from telegram import (ForceReply, InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardMarkup, ReplyKeyboardRemove, Update)
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, ConversationHandler, Filters,
                          MessageHandler, Updater)

#########################################################################################################################################################################################
mydb = mysql.connector.connect(
    host="localhost",  # 数据库主机地址
    user="root",  # 数据库用户名
    passwd="",  # 数据库密码
    database=""  # 数据库名
)

TGTOKEN = ''
SVM_IP_ADDRESS = ''
SVM_API_ID = ''
SVM_API_KEY = ''
#########################################################################################################################################################################################
solus = SolusVM(SVM_IP_ADDRESS, SVM_API_ID, SVM_API_KEY)
bot = telegram.Bot(token=TGTOKEN)
mycursor = mydb.cursor()
updater = Updater(token=TGTOKEN, use_context=True)
dispatcher = updater.dispatcher
# logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)
#

clientEcho, clientButton, cancel, Path, adminEcho, cdkey, clientChooseVS, clientChooseVSReply = range(8)


def start(update: Update, context: CallbackContext) -> int:
    # context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")
    # reply_keyboard = [['47', '48', '49']]

    reply_keyboard = [['Client', 'Admin', 'GetChatID']]
    update.message.reply_text(
        'Hi! 我是一个可以用于辅助SolusVM的机器人\n'
        '请选择你的身份，普通用户请选择Client\n获取您的chatid请选择GetChatID',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Path'
        ),
    )
    return Path


def Path(update: Update, context: CallbackContext) -> int:
    if (update.message.text == 'Client'):
        myresult = dbReadClient(chat_id1=update.effective_chat.id)
        update.message.reply_text(myresult)  # debug
        if (myresult != []):
            if (str(update.effective_chat.id) == myresult[0][1]):
                if (myresult[0][2] == 'Active'):
                    global ClientIfActiveAndIfInDB
                    ClientIfActiveAndIfInDB = True
                    reply_keyboard = [['Continue']]
                    update.message.reply_text(
                        '您是已知用户，请点击Continue来继续',
                        reply_markup=ReplyKeyboardMarkup(
                            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Continue as client'
                        ),
                    )
                    return clientChooseVS
                elif (myresult[0][2] == 'Disabled'):
                    update.message.reply_text(
                        'Hi! 我是一个可以用于辅助SolusVM的机器人\n '
                        '<b>很抱歉，您的账户已经被停用或已被封禁。</b>',
                        reply_markup=ReplyKeyboardRemove(),
                        parse_mode='HTML'
                    )
                    return ConversationHandler.END
        else:
            reply_keyboard = [['CDKEY', 'Cancel']]
            update.message.reply_text(
                'Hi! 我是一个可以用于辅助SolusVM的机器人\n'
                '如果您要兑换您的卡密(CDKEY)，请点击CDKEY；\n如果您想结束本次对话，请点击Cancel。\n',
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True, input_field_placeholder='Please choose.'
                ),
            )
            return ClientEcho
    elif (update.message.text == 'Admin'):
        myresult = dbReadAdmin(chat_id1=update.effective_chat.id)
        update.message.reply_text(myresult)  # debug
        if (myresult != []):
            if (str(update.effective_chat.id) == myresult[0][1]):
                reply_keyboard = [['Continue']]
                update.message.reply_text(
                    'Hi! 我是一个可以用于辅助SolusVM的机器人\n'
                    '你是已知的管理员，请直接点击Continue继续。',
                    reply_markup=ReplyKeyboardMarkup(
                        reply_keyboard, one_time_keyboard=True, input_field_placeholder='Continue as admin'
                    ),
                )
                return adminEcho

        else:
            update.message.reply_text(
                'Hi! 我是一个可以用于辅助SolusVM的机器人\n '
                '<b>未知管理员。<b/>',
                reply_markup=ReplyKeyboardRemove(),
                parse_mode='HTML'
            )
            return ConversationHandler.END
    elif (update.message.text == 'GetChatID'):
        update.message.reply_text(
            '您的chat id是：\n<b>' + str(update.effective_chat.id) + '</b>',
            reply_markup=ReplyKeyboardRemove(),
            parse_mode='HTML'
        )
        return ConversationHandler.END


def unknown(update, context) -> int:
    context.bot.send_message(chat_id=update.effective_chat.id, text="抱歉，未知命令或出现错误。")


def cancel(update, context) -> int:
    update.message.reply_text('Bye!')
    return ConversationHandler.END


def dbReadClient(chat_id1):
    sql = "SELECT * FROM clientInf WHERE client_chat_id = %s"
    na = (chat_id1,)
    mycursor.execute(sql, na)
    myresult = mycursor.fetchall()
    mydb.commit()
    return myresult


def dbReadClientVS(chat_id1):
    sql = "SELECT * FROM vmInf WHERE client_chat_id = %s"
    na = (chat_id1,)
    mycursor.execute(sql, na)
    myresult = mycursor.fetchall()
    mydb.commit()
    return myresult


def dbReadVSByMainId(mainId):
    sql = "SELECT * FROM vmInf WHERE mainId = %s"
    na = (mainId,)
    mycursor.execute(sql, na)
    myresult = mycursor.fetchall()
    mydb.commit()
    return myresult


def dbReadMasterInf(svmMasterId):
    sql = "SELECT * FROM svmMasterInf WHERE svmMasterId = %s"
    na = (svmMasterId,)
    mycursor.execute(sql, na)
    myresult = mycursor.fetchall()
    mydb.commit()
    global SVM_IP_ADDRESS, SVM_API_ID, SVM_API_KEY
    SVM_IP_ADDRESS = myresult[0][1]
    SVM_API_ID = myresult[0][2]
    SVM_API_KEY = myresult[0][3]
    return


def dbReadCdkey(cdkey):
    sql = "SELECT * FROM cdkeyInf WHERE cdkey = %s"
    na = (cdkey,)
    mycursor.execute(sql, na)
    myresult = mycursor.fetchall()
    mydb.commit()
    if (myresult[0][2] == 'True'):
        secsql = "INSERT INTO userInf (cdkeyId, ifVaild) VALUES (%s, 'False')"
        secval = (myresult[0][0],)
        mycursor.execute(secsql, secval)
        mydb.commit()
        ret = str(myresult[0][3])
        return ret
    else:
        ret = 'Invaild'
        return ret


def dbReadAdmin(chat_id1):
    sql = "SELECT * FROM adminInf WHERE admin_chat_id = %s"
    na = (chat_id1,)
    mycursor.execute(sql, na)
    myresult = mycursor.fetchall()
    mydb.commit()
    return myresult

def dbReadVSExpireTIme(nowTime):
    sql = "SELECT * FROM vmInf WHERE expire_time = %s"
    na = (nowTime,)
    mycursor.execute(sql, na)
    myresult = mycursor.fetchall()
    mydb.commit()
    return myresult



def dbWriteSVMInf(SVM_IP_ADDRESS, SVM_API_ID, SVM_API_KEY):
    sql = "INSERT INTO userInf (SVM_IP_ADDRESS, SVM_API_ID ,SVM_API_KEY) VALUES (%s, %s, %s)"
    val = (SVM_IP_ADDRESS, SVM_API_ID, SVM_API_KEY)
    mycursor.execute(sql, val)
    mydb.commit()
    return


def clientChooseVS(update: Update, context: CallbackContext) -> int:
    myresult = dbReadClientVS(chat_id1=update.effective_chat.id)
    update.message.reply_text(len(myresult))
    if (len(myresult) == 0):
        update.message.reply_text('抱歉，未找到您的虚拟机！')
        return ConversationHandler.END
    else:
        mes = ''
        reply_keyboard = []
        for i in range(len(myresult)):
            if (myresult[i][6] == 'Active'):
                mes += 'ID: ' + str(myresult[i][0]) + ' 产品详情： ' + str(myresult[i][4]) + '\n'
            elif (myresult[i][6] != 'Active'):
                mes += '<b>已失效产品（不可操作）：</b> \n'
                mes += 'ID: ' + str(myresult[i][0]) + ' 产品详情： ' + str(myresult[i][4]) + '\n'

        for i in range(len(myresult)):
            if (myresult[i][6] == 'Active'):
                reply_keyboard.append(str(myresult[i][0]))
                # pass

        update.message.reply_text(text=mes, parse_mode='HTML')
        update.message.reply_text(
            '请选择您本次想要操作的的虚拟机ID。',
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, input_field_placeholder='Please choose one produce.'
            ),
        )

        return clientChooseVSReply


def clientChooseVSReply(update: Update, context: CallbackContext) -> int:
    global mainId
    mainId = update.message.text
    myresult = dbReadVSByMainId(mainId)
    global vsid1
    vsid1 = myresult[0][2]
    update.message.reply_text(vsid1)
    dbReadVSByMainId(mainId=myresult[0][1])
    reply_keyboard = [['Continue']]
    update.message.reply_text(
        '请点击Continue以继续。',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Continue'
        ),
    )
    return clientEcho


def clientEcho(update: Update, context: CallbackContext) -> int:
    if (ClientIfActiveAndIfInDB == True):

        update.message.reply_text(dbReadVSByMainId(mainId))
        update.message.reply_text(text=queryVMStatus(vsid1), parse_mode='HTML')
        vms1 = solus.virtualServerState(vserverid=vsid1)
        if (str(vms1['type']) == 'openvz'):
            keyboard = [
                [InlineKeyboardButton("⤴️开机", callback_data='bootVM')],
                [InlineKeyboardButton("⤵️关机", callback_data='shutdownVM')],
                [InlineKeyboardButton("🔄重启", callback_data='rebootVM')],
                [
                    InlineKeyboardButton("打开TUN/TAP", callback_data='tunOn'),
                    InlineKeyboardButton("关闭TUN/TAP", callback_data='tunOff'),
                ],
                [
                    InlineKeyboardButton("打开串行控制台", callback_data='enableSC'),
                    InlineKeyboardButton("立刻关闭串行控制台", callback_data='disableSC')
                ],
                [InlineKeyboardButton("➡️打开面板", url='https://' + SVM_IP_ADDRESS)],
                [InlineKeyboardButton("跳过（不执行任何操作）", callback_data='pass')],
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('请选择您想执行的操作:', reply_markup=reply_markup)
        return clientButton
    else:
        if (update.message.text == 'CDKEY'):
            update.message.reply_text(text='请输入您的CDKEY', reply_markup=ReplyKeyboardRemove())
            return cdkey
        else:
            update.message.reply_text(text='Bye!', reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END


def clientCdkey(update: Update, context: CallbackContext) -> int:
    return ConversationHandler.END


def adminEcho(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        '欢迎来到管理后台，\n<b>您今天想要做些什么呢？</b>',
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='HTML'
    )
    mes = '1.添加新主控服务器\n2.创建新卡密\n3.手动为客户分配新产品'
    update.message.reply_text(mes)
    reply_keyboard = [['1', '2', '3']]
    update.message.reply_text(
        '请选择序号以继续。',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Continue'
        ),
    )
    return adminReply


def cdkey(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("开发中。。。")
    return ConversationHandler.END


def adminReply(update: Update, context: CallbackContext) -> int:
    if (update.message.text == '1'):
        update.message.reply_text(
            '请务必按照如下格式输入您的数据\n'
            'SolusVM的主控地址,API的ID,API的Key\n'
            '请注意必须按照指定格式输入，使用英文逗号，不要多加类似空格的多余字符，否则有可能操作将失败！',
            reply_markup=ReplyKeyboardRemove()
        )
        return adminReplyAddNewSVMMaster
    elif (update.message.text == '2'):
        update.message.reply_text(
            '请进入DB手动操作！\n',
            reply_markup=ReplyKeyboardRemove()
        )
    elif (update.message.text == '3'):
        update.message.reply_text(
            '请进入DB手动操作！\n',
            reply_markup=ReplyKeyboardRemove()
        )
    return ConversationHandler.END


def addNewVS(update: Update, context: CallbackContext) -> int:
    return ConversationHandler.END


def adminReplyAddNewSVMMaster(update: Update, context: CallbackContext) -> int:
    retmes = update.message.text
    retmes1 = retmes.split(',')
    dbWriteSVMInf(SVM_IP_ADDRESS=retmes1[0], SVM_API_ID=retmes1[1], SVM_API_KEY=retmes1[2])
    update.message.reply_text('成功')
    return ConversationHandler.END


def clientButton(update: Update, context: CallbackContext) -> int:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    query.answer()
    queryAnswer = query.data

    if (queryAnswer == 'tunOn'):
        ret = solus.enableTUN(vserverid=vsid1)
    elif (queryAnswer == 'tunOff'):
        ret = solus.disableTUN(vserverid=vsid1)
    elif (queryAnswer == 'bootVM'):
        ret = solus.bootVirtualServer(vserverid=vsid1)
    elif (queryAnswer == 'shutdownVM'):
        ret = solus.shutdownVirtualServer(vserverid=vsid1)
    elif (queryAnswer == 'rebootVM'):
        ret = solus.rebootVirtualServer(vserverid=vsid1)
    elif (queryAnswer == 'enableSC'):
        ret = solus.toggleSerialConsole(vserverid=vsid1, access='enable')
        if (ret['created'] == 'success'):
            retMes = ''
            retMes += '串行控制台IP: ' + str(ret['consoleip']) + '\n'
            retMes += '串行控制台端口: ' + str(ret['consoleport']) + '\n'
            retMes += '串行控制台用户名: ' + str(ret['consoleusername']) + '\n'
            retMes += '串行控制台密码: ' + str(ret['consolepassword']) + '\n'
            retMes += '本次会话过期时间: ' + str('%.1f' % (int(ret['sessionexpire']) / 60)) + 'minutes\n'
            query.message.reply_text(text=retMes)
        else:
            retMes = '抱歉，操作失败，可能是由于已经创建了一个串行控制台，\n请尝试先关闭一次串行控制台再开启。'
            query.message.reply_text(text=retMes)
    elif (queryAnswer == 'disableSC'):
        ret = solus.toggleSerialConsole(vserverid=vsid1, access='disable')
    elif (queryAnswer == 'pass'):
        query.edit_message_text(text='Pass')
        ret = ''

    if (ret != ''):
        if (ret['status'] == 'success'):
            query.edit_message_text(text=queryAnswer)
        else:
            query.edit_message_text(text=f"ERROR!")
    # return clientEcho
    return ConversationHandler.END


def queryVMStatus(vsid):
    vms = solus.virtualServerInfo(vserverid=vsid)
    vms1 = solus.virtualServerState(vserverid=vsid)
    myresult = dbReadVSByMainId(mainId)
    ret = ''
    if (vms['status'] == 'success'):
        if (str(vms1['state']) == 'None'):
            ret += '状态: <b>在线</b>''\n'
        else:
            ret += '状态: <b>离线</b>' + '\n'
        ret += '虚拟化类型:  ' + str(vms1['type']) + '\n'
        '''
        基础规则是 10.0.1.D 的内网IP（D最多是3位数）
        SSH端口是 61D（D不足3位前面补0）
        可用端口是 1D0 - 1D9（D不足3位前面补0）
        具体案例： 10.0.1.56
        SSH端口是 61056
        可用端口是 10561 - 10569
        '''

        if (True):
            mainip = vms1['mainipaddress']
            aa1 = mainip.split('.')
            D1 = str(aa1[3])
            if (len(D1) == 1):
                D2 = '00' + D1
            elif (len(D1) == 2):
                D2 = '0' + D1
            elif (len(D1) == 3):
                D2 = D1
            ret += 'SSH端口: 61' + D2 + '\n'
            ret += '可用端口范围: 1' + D2 + '0 - 1' + D2 + '9\n'
        ret += '核心个数:  ' + str(vms['cpus']) + '\n'
        a1 = vms1["memory"].split(",")
        ret += 'RAM: 已使用/总 RAM:  ' + str('%.1f' % (int(a1[1]) / 1024 / 1024)) + 'MB/' + str(
            '%.1f' % (int(a1[0]) / 1024 / 1024)) + 'MB  ' + str(a1[3]) + '% | '
        ret += str('%.1f' % (int(a1[2]) / 1024 / 1024)) + 'MB Free\n'
        a2 = vms1["hdd"].split(",")
        ret += '硬盘: 已使用/总 硬盘:  ' + str('%.1f' % (int(a2[1]) / 1024 / 1024 / 1024)) + 'GB/' + str(
            '%.1f' % (int(a2[0]) / 1024 / 1024 / 1024)) + 'GB  ' + str(a2[3]) + '% | '
        ret += str('%.1f' % (int(a2[2]) / 1024 / 1024 / 1024)) + 'GB Free\n'
        a3 = vms1["bandwidth"].split(",")
        ret += '流量: 已使用/总 流量:  ' + str('%.1f' % (float(a3[1]) / 1024 / 1024 / 1024 / 1024)) + 'TB/' + str(
            '%.1f' % (float(a3[0]) / 1024 / 1024 / 1024 / 1024)) + 'TB  ' + str(a3[3]) + '% | '
        ret += str('%.1f' % (int(a3[2]) / 1024 / 1024 / 1024 / 1024)) + 'TB Free\n'
        ret += '节点:  ' + str(vms1['node']) + '\n'
        # ret+='DEBUG:\n'+str(vms1)
        return ret
    else:
        ret = '抱歉，当前无法处理您的请求！错误信息如下:\n' + vms1['statusmsg']
        return ConversationHandler.END


def scheduleTask_removeVS():
    nowTime=time.time()

    pass


def startScheduleTasks():
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduleTask_removeVS, 'interval', seconds=300)  # 间隔3秒钟执行一次
    scheduler.start()


def main():
    startScheduleTasks()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start, filters=Filters.chat_type.private)],
        states={
            clientChooseVS: [MessageHandler(Filters.chat_type.private & Filters.text, clientChooseVS)],
            clientChooseVSReply: [MessageHandler(Filters.chat_type.private & Filters.text, clientChooseVSReply)],
            clientEcho: [MessageHandler(Filters.chat_type.private & Filters.text, clientEcho)],
            adminEcho: [MessageHandler(Filters.chat_type.private & Filters.text, adminEcho)],
            Path: [MessageHandler(Filters.chat_type.private & Filters.text, Path)],
            cdkey: [MessageHandler(Filters.chat_type.private & Filters.text, cdkey)],

            clientButton: [CallbackQueryHandler(clientButton)],
            # cancel:[CommandHandler('cancel', cancel)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        conversation_timeout=60.0
    )

    dispatcher.add_handler(conv_handler)
    #
    updater.start_polling()
    updater.idle()
    ##


if __name__ == '__main__':
    main()
