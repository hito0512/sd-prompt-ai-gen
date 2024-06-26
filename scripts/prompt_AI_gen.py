'''
# -*- encoding: utf-8 -*-
# 说明    : 提示词生成器
# 时间    : 2024/05/31 17:29:23
# 作者    : Hito
# 版本    : 1.0
# 环境    : python: 3.8.10
'''

import requests
import modules
from modules import images, paths, script_callbacks, scripts, shared,ui_toprow
import gradio as gr
import textwrap
import json
import os


class Script(scripts.Script):
    def __init__(self):
        super().__init__()
        self.guide = False
        self.base_ip = shared.opts.data.get('base_ip', '127.0.0.1')
        self.port = shared.opts.data.get('ollama_port', '11434')
        self.base_url = f'http://{self.base_ip}:{self.port}/v1/chat/completions'
        self.params = {'select_model':''}

        self.models = self.update_text_model_list()
        
        
        self.prime_directive = textwrap.dedent("""\
            Act as a prompt maker with the following guidelines:
            - Break keywords by commas.
            - Provide high-quality, non-verbose, coherent, brief, concise, and not superfluous prompts.
            - Focus solely on the visual elements of the picture; avoid art commentaries or intentions.
            - Construct the prompt with the component format:
            1. Start with the subject and keyword description.
            2. Follow with scene keyword description.
            3. Finish with background and keyword description.
            - Limit yourself to no more than 7 keywords per component  
            - Include all the keywords from the user's request verbatim as the main subject of the response.
            - Be varied and creative.
            - Always reply on the same line and no more than 100 words long. 
            - Do not enumerate or enunciate components.
            - Do not include any additional information in the response.                                                       
            The followin is an illustartive example for you to see how to construct a prompt your prompts should follow this format but always coherent to the subject worldbuilding or setting and cosider the elemnts relationship.
            Example:
            Subject: Demon Hunter, Cyber City.
            prompt: A Demon Hunter, standing, lone figure, glow eyes, deep purple light, cybernetic exoskeleton, sleek, metallic, glowing blue accents, energy weapons. Fighting Demon, grotesque creature, twisted metal, glowing red eyes, sharp claws, Cyber City, towering structures, shrouded haze, shimmering energy.                             
            Make a prompt for the following Subject:
            """)
    def title(self):
        return "Prompt_AI_Gen"
    
    def show(self, is_img2img):
        return scripts.AlwaysVisible
    
         
    def ui(self, is_img2img):
        with gr.Accordion("Prompt AI Gen",open=False):
            with gr.Group():
                with gr.Row(scale=1, min_width=100):
                    select_text_model = gr.Dropdown(label="Text-Model", choices=self.models,value='')
                with gr.Column(scale=2, min_width=400):
                    input_prompt = gr.Textbox(label="主题描述 :[谁？在哪里？]",value='Demon Hunter, Cyber City')
                    output_prompt = gr.Textbox(label="AI 生成")
                with gr.Row():
                    gen_text_button = gr.Button(value="AI Gen prompt",variant='primary')
                    send_text_button = gr.Button(value="send to prompt",variant='primary')
                
        gen_text_button.click(self.generate_text,input_prompt, output_prompt)
        send_text_button.click(self.send2prompt, output_prompt, None)
        select_text_model.change(lambda x: self.params.update({'select_model':x}), select_text_model, None)
    
    def send2prompt(self,input_prompt):
        if input_prompt:
            demo = shared.demo
            # ui_toprow.prompt.value = input_prompt txt2img_paste_fields
            # modules.ui.txt2img_paste_fields[0] = PasteField(input_prompt, "Prompt", api="prompt"),
            print(len(demo.blocks))
            print('***-------***', demo.blocks[5].elem_id, demo.blocks[5].elem_classes)
            # for i in range(len(demo.blocks)):
            #     try:
            #         print('***-------***', i, (demo.blocks[i].elem_id),'------------  ', demo.blocks[i].elem_classes)
            #     except:
                    # ...
            # print('***-------***', shared.prompt_styles)  
    def send_request(self, data, headers, **kwargs):
        headers = kwargs.get('headers', {"Content-Type": "application/json"})
        response = requests.post(self.base_url, headers=headers, json=data)
        
        if response.status_code == 200:
            return response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
        else:
            print(f"Error: Request to ollama failed with status code {response.status_code}")
            return None
        
    def generate_text(self,input_prompt):
        data = {
                'model': self.params['select_model'],
                'messages': [
                    {"role": "system", "content": self.prime_directive},
                    {"role": "user", "content": input_prompt}
                ],  
            }

        generated_text = self.send_request(data, headers={"Content-Type": "application/json"})
        return generated_text
            
    def update_text_model_list(self):
        api_url = f'http://{self.base_ip}:{self.port}/api/tags'
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            all_models = [model['name'] for model in response.json()['models']]
        except Exception as e:
            print(f"Failed to fetch models from Ollama: {e}")

        
        return all_models

