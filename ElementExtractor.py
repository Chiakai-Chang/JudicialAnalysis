# -*- coding: utf-8 -*-
"""
Created on Fri Mar  8 11:33:55 2024

@author: Chiakai
"""

import os
import json
import re
import ftfy
import time

# 將全形英文字母轉成半形
def full_to_half_width(text):
    """全形轉半形"""
    result = ""
    for char in text:
        code = ord(char)
        if code == 0x3000:  # 空格特殊處理
            code = 0x20
        elif 0xFF01 <= code <= 0xFF5E:  # 全形字符（不包括空格）轉換
            code -= 0xFEE0
        result += chr(code)
    return result

class Judicial_Parser:
    
    def wash(self, repeat=3):
        jfull_raw = f'{self.semi_raw}'
        
        # 先將全部英文全形轉半形
        jfull_raw = full_to_half_width(jfull_raw)
        
        # 再將全部數字全形轉半形
        big_numbers = {
            '０' : '0',
            '１' : '1', 
            '２' : '2', 
            '３' : '3', 
            '４' : '4', 
            '５' : '5', 
            '６' : '6', 
            '７' : '7', 
            '８' : '8', 
            '９' : '9',
            }
        for bnF, bnS in big_numbers.items():
            jfull_raw = jfull_raw.replace(bnF, bnS)
        
        # 準備標準化輸入
        chinese_numbers = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]

        # 不知道為什麼有些步驟會失效，故重複做個幾次
        for _ in range(repeat):
            # 找出所有包含\r\n但卻是把正確意思切開的
            to_fixes = re.findall('\S\r\n\S', jfull_raw)
    
            fixes = dict()
            
            for tf in to_fixes:
                # 如果後面以下情形，應該是真的句子的結果，不處理跳過
                if tf[-1] in chinese_numbers:
                    fixes[tf] = tf.replace('\r\n', ' ')
                elif tf == '號\r\n移':
                    fixes[tf] = tf.replace('\r\n', ' ')
                else:
                    fixes[tf] = tf.replace('\r\n', '')
    
            for k, v in fixes.items():
                jfull_raw = jfull_raw.replace(k, v)    
    
            # 手動整理已知問題
            jfull_raw = jfull_raw.replace('主 文', '主文 ')\
                .replace('法 官', '法官 ')\
                .replace('理 由', '理由 ')\
                .replace(' 事實理由及證據', '事實理由及證據')\
                .replace('扣押物品 收據證明書', '扣押物品收據證明書')\
                .replace('事 實 理 由 及 證 據', '事實理由及證據')\
                .replace('中 華 民 國', '中華民國')
                    
            # 整理數字前後有空格的問題
            to_fixes_n = re.findall('\d ', jfull_raw)
            for t in to_fixes_n:
                jfull_raw = jfull_raw.replace(t, t.replace(' ', ''))
    
            to_fixes_n = re.findall(' \d', jfull_raw)
            for t in to_fixes_n:
                jfull_raw = jfull_raw.replace(t, t.replace(' ', ''))
                
            to_fixes_n = re.findall(' \d+ ', jfull_raw)
            for t in to_fixes_n:
                jfull_raw = jfull_raw.replace(t, t.replace(' ', ''))
                
            # 手動整理已知問題
            jfull_raw = jfull_raw.replace('。。', '。')\
                .replace(' 。', '。')\
                .replace('。 ', '。')\
                .replace(' ，', '，')\
                .replace('， ', '，')\
                .replace(' 、', '，')\
                .replace('、 ', '，')
                
            # 多餘的空格都只留一個
            while '  ' in jfull_raw:
                jfull_raw = jfull_raw.replace('  ', ' ')
    
            # (不知道為什麼沒效果需要再一次)手動整理已知問題
            jfull_raw = jfull_raw.replace('主 文', '主文 ')\
                .replace('法 官', '法官 ')\
                .replace('理 由', '理由 ')\
                .replace('中 華 民 國', '中華民國')\
                .replace(' 事實理由及證據', '事實理由及證據')\
                .replace('扣押物品 收據證明書', '扣押物品收據證明書')\
                .replace('事 實 理 由 及 證 據', '事實理由及證據')\
                .replace('中 華 民 國', '中華民國')\
                .replace('。。', '。')\
                .replace(' 。', '。')\
                .replace('。 ', '。')\
                .replace(' ，', '，')\
                .replace('， ', '，')\
                .replace(' 、', '，')\
                .replace('、 ', '，')
    
            # (不知道為什麼沒效果需要再一次) 多餘的空格都只留一個
            while '  ' in jfull_raw:
                jfull_raw = jfull_raw.replace('  ', ' ')
        self.text = jfull_raw
    
    def __init__(self, json_data:dict):
        self.json_data = json_data
        self.raw = json_data.get('JFULL', '')
        date = time.strptime(json_data.get('JDATE'), '%Y%m%d')
        self.date = date
        self.dateSTR = time.strftime('%Y-%m-%d', date)
        self.jid = json_data.get('JID', '')
        self.title = json_data.get('JTITLE', '')
        
        self.semi_raw = self.raw.strip().replace('\u3000', '').replace('\r\n\r\n', '。').replace('。\r\n', '。').replace('\r\n。', '。').replace('：\r\n', '。').replace('\r\n（', '（').replace('\r\n    ', '')
        self.wash()
        self.text_u = ftfy.fix_text(self.text)

if __name__ == '__main__':
    source_file = os.path.join(
        'C:\\', '課程', '交大','論文','案件整理',
        'json_files.txt'
        )
    
    passon = 17
    with open(source_file, 'r', encoding='utf-8') as f:
        # 2022~2023年判決書有211萬7,454個json檔
        # 故一次讀一個處理，減少記憶體占用
        raw_data = ''
      
        while 1: 
            file = f.readline()
            
            if '刑事' in file:
                if not ('簡易' in file or '民事' in file or '補償' in file or '憲法' in file or '商業' in file):
                    if passon > 0:
                        passon -= 1 
                        file = f.readline()
                        continue
                    else:
                        break
            
        file = file.strip()
            
        with open(file, 'r', encoding='utf-8') as jf:
            json_data = json.load(jf)
    
    parser = Judicial_Parser(json_data)
    
    raw = parser.raw
    text = parser.text
    text_u = parser.text_u