import tkinter as tk
from tkinter import ttk, messagebox, font
import random
from collections import Counter
from functools import partial

class Card:
    def __init__(self, suit, value):
        self.suit = suit
        self.value = value

    def __str__(self):
        return f"{self.value}{self.suit}"

    def __repr__(self):
        return self.__str__()

    def get_numeric_value(self):
        mapping = {
            '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
            'J': 11, 'Q': 12, 'K': 13, 'A': 14, '2': 15
        }
        return mapping[self.value]

    def get_suit_value(self):
        return {'♠': 1, '♣': 2, '♦': 3, '♥': 4}[self.suit]

class SpecialSkill:
    def __init__(self, name, description, effect_type, value=0):
        self.name = name
        self.description = description
        self.effect_type = effect_type  # 'draw', 'discard', 'skip', 'reverse', 'peek', 'swap', 'shield'
        self.value = value

class Player:
    def __init__(self, name, is_human=False):
        self.name = name
        self.cards = []
        self.is_human = is_human
        self.special_skills = []
        self.shield_active = False  # Protection from negative effects
        self.skip_next_turn = False

    def add_card(self, card):
        self.cards.append(card)

    def remove_cards(self, cards):
        for c in cards:
            if c in self.cards:
                self.cards.remove(c)

    def add_skill(self, skill):
        self.special_skills.append(skill)

    def use_skill(self, skill):
        if skill in self.special_skills:
            self.special_skills.remove(skill)
            return True
        return False

    def sort_cards(self):
        self.cards.sort(key=lambda c: (c.get_numeric_value(), c.get_suit_value()))

class GameLogic:
    def __init__(self):
        self.suits = ['♠', '♣', '♦', '♥']
        self.values = ['3','4','5','6','7','8','9','10','J','Q','K','A','2']
        self.special_skills = [
            SpecialSkill("🎯 Sniper", "Force target player to discard their highest card", "force_discard"),
            SpecialSkill("🛡️ Shield", "Protect yourself from next negative effect", "shield"),
            SpecialSkill("👁️ Peek", "View another player's cards", "peek"),
            SpecialSkill("🔄 Swap", "Swap 2 random cards with target player", "swap"),
            SpecialSkill("⏭️ Skip", "Skip target player's next turn", "skip"),
            SpecialSkill("🎲 Chaos", "All players pass 1 card to next player", "chaos"),
            SpecialSkill("💎 Draw Lucky", "Draw the lowest card from deck", "draw_lucky"),
            SpecialSkill("🃏 Wild Play", "Play any card regardless of rules", "wild_play"),
        ]

    def create_deck(self):
        deck = [Card(s, v) for s in self.suits for v in self.values]
        random.shuffle(deck)
        return deck

    def get_combo_type(self, cards):
        if not cards:
            return None, 0
            
        vals = [c.get_numeric_value() for c in cards]
        suits = [c.suit for c in cards]
        n = len(cards)
        
        if n == 1:
            return 'single', vals[0]
        if n == 2 and vals[0] == vals[1]:
            return 'pair', vals[0]
        if n == 3 and len(set(vals)) == 1:
            return 'triple', vals[0]
        if n == 5:
            is_flush = len(set(suits)) == 1
            sorted_vals = sorted(vals)
            is_straight = all(sorted_vals[i] + 1 == sorted_vals[i+1] for i in range(4))
            counts = sorted(Counter(vals).values())
            
            if is_straight and is_flush:
                return 'straight_flush', max(vals)
            if counts == [1, 4]:
                return 'four_of_a_kind', max(vals, key=vals.count)
            if counts == [2, 3]:
                return 'full_house', max(vals, key=vals.count)
            if is_flush:
                return 'flush', max(vals)
            if is_straight:
                return 'straight', max(vals)
        return None, 0

    def is_valid_play(self, cards, last_cards, last_type, last_val, is_first_round, wild_play=False):
        if not cards:
            return False
            
        combo, value = self.get_combo_type(cards)
        if not combo:
            return False
            
        # Wild play skill bypasses all rules except first round 3♠
        if wild_play and not is_first_round:
            return True
            
        # Rule for 3♠ only applies to the first round of the game
        if is_first_round and not any(c.value == '3' and c.suit == '♠' for c in cards):
            return False
            
        if not last_cards:
            return True
            
        # After three passes, any valid combination is allowed
        if not last_type:
            return True
            
        # Compare combination type and value
        if combo != last_type:
            return False
            
        return value > last_val

class BigTwoGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🃏 Remi Big Two Game - Special Edition")
        self.root.geometry("1400x900")
        self.root.configure(bg='#0d4f3c')
        self.root.state('zoomed')
        
        self.root.resizable(True, True)
        self.root.minsize(1200, 800)

        self.logic = GameLogic()
        self.players = [Player("You", True)] + [Player(f"AI Player {i}") for i in range(1, 4)]
        self.current = 0
        self.last_cards = []
        self.last_type = None
        self.last_val = 0
        self.pass_count = 0
        self.selected = []
        self.over = False
        self.is_first_round = True
        self.starter_index = None
        self.first_play_made = False
        self.round_count = 0
        self.skill_phase = False
        self.available_skills = []
        self.pending_skill = None
        self.deck = []
        self.wild_play_active = False

        # Fonts
        self.card_font = font.Font(family="Arial", size=10, weight="bold")
        self.suit_font = font.Font(family="Arial", size=16)
        self.title_font = font.Font(family="Arial", size=20, weight="bold")
        self.info_font = font.Font(family="Arial", size=11)
        self.player_font = font.Font(family="Arial", size=10, weight="bold")

        self.setup_ui()
        self.new_game()
        self.root.mainloop()

    def setup_ui(self):
        # Main container
        self.root.grid_rowconfigure(0, weight=0)  # Header
        self.root.grid_rowconfigure(1, weight=0)  # Info
        self.root.grid_rowconfigure(2, weight=1)  # Main game area
        self.root.grid_rowconfigure(3, weight=0)  # Skills area
        self.root.grid_rowconfigure(4, weight=0)  # Player cards
        self.root.grid_rowconfigure(5, weight=0)  # Controls
        self.root.grid_columnconfigure(0, weight=1)

        # Header
        header = tk.Frame(self.root, bg='#0d4f3c', height=80)
        header.grid(row=0, column=0, sticky='ew', padx=10, pady=5)
        header.grid_propagate(False)
        
        tk.Label(header, text="🃏 REMI BIG TWO - SPECIAL EDITION", bg='#0d4f3c', fg='gold', 
                font=self.title_font).pack(pady=2)
        tk.Label(header, text="Urutan: 3→4→5→6→7→8→9→10→J→Q→K→A→2 | Special Skills setiap 4 putaran!", 
                bg='#0d4f3c', fg='white', font=self.info_font).pack()

        # Game info
        info_frame = tk.Frame(self.root, bg='#0d4f3c', height=40)
        info_frame.grid(row=1, column=0, sticky='ew', padx=10, pady=2)
        info_frame.grid_propagate(False)
        
        self.cur_lbl = tk.Label(info_frame, text="Current: You", bg='#0d4f3c', fg='white', 
                               font=self.info_font)
        self.cur_lbl.pack(side=tk.LEFT, padx=15)
        
        self.combo_lbl = tk.Label(info_frame, text="Combo: -", bg='#0d4f3c', fg='white', 
                                font=self.info_font)
        self.combo_lbl.pack(side=tk.LEFT, padx=15)
        
        self.pass_lbl = tk.Label(info_frame, text="Pass Count: 0", bg='#0d4f3c', fg='white', 
                               font=self.info_font)
        self.pass_lbl.pack(side=tk.LEFT, padx=15)
        
        self.round_lbl = tk.Label(info_frame, text="Round: 1", bg='#0d4f3c', fg='gold', 
                                font=self.info_font)
        self.round_lbl.pack(side=tk.RIGHT, padx=15)

        # Main game area
        main_container = tk.Frame(self.root, bg='#0d4f3c')
        main_container.grid(row=2, column=0, sticky='nsew', padx=10, pady=5)
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_rowconfigure(1, weight=2)
        main_container.grid_columnconfigure(0, weight=1)

        # AI Player 1 (top)
        ai1_frame = tk.Frame(main_container, bg='#1a5f4a', bd=2, relief='raised')
        ai1_frame.grid(row=0, column=0, sticky='ew', pady=(0, 5))
        ai1_frame.grid_columnconfigure(1, weight=1)
        
        tk.Label(ai1_frame, text="AI Player 1", bg='#1a5f4a', fg='white', 
                font=self.player_font).grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.player2_count = tk.Label(ai1_frame, text="13 cards", bg='#1a5f4a', fg='gold', 
                                    font=self.info_font)
        self.player2_count.grid(row=0, column=2, sticky='e', padx=5, pady=2)
        
        self.player2_cards = tk.Frame(ai1_frame, bg='#1a5f4a')
        self.player2_cards.grid(row=1, column=0, columnspan=3, sticky='ew', padx=5, pady=2)

        # Middle section
        middle_container = tk.Frame(main_container, bg='#0d4f3c')
        middle_container.grid(row=1, column=0, sticky='nsew')
        middle_container.grid_rowconfigure(0, weight=1)
        middle_container.grid_columnconfigure(0, weight=1)
        middle_container.grid_columnconfigure(1, weight=3)
        middle_container.grid_columnconfigure(2, weight=1)

        # AI Player 2 (left)
        left_frame = tk.Frame(middle_container, bg='#1a5f4a', bd=2, relief='raised')
        left_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        tk.Label(left_frame, text="AI Player 2", bg='#1a5f4a', fg='white', 
                font=self.player_font).pack(anchor='w', padx=5, pady=2)
        
        self.player3_cards = tk.Frame(left_frame, bg='#1a5f4a')
        self.player3_cards.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.player3_count = tk.Label(left_frame, text="13 cards", bg='#1a5f4a', fg='gold', 
                                    font=self.info_font)
        self.player3_count.pack(anchor='e', padx=5, pady=2)

        # Center area
        center_frame = tk.Frame(middle_container, bg='#2d5a27', bd=3, relief='sunken')
        center_frame.grid(row=0, column=1, sticky='nsew', padx=5)
        center_frame.grid_rowconfigure(2, weight=1)
        center_frame.grid_columnconfigure(0, weight=1)
        
        tk.Label(center_frame, text="LAST PLAYED CARDS", bg='#2d5a27', fg='gold', 
                font=('Arial', 14, 'bold')).grid(row=0, column=0, pady=5)
        
        self.last_lbl = tk.Label(center_frame, text="None", bg='#2d5a27', fg='white', 
                               font=self.info_font)
        self.last_lbl.grid(row=1, column=0, pady=2)
        
        # Fixed center cards frame
        center_scroll_frame = tk.Frame(center_frame, bg='#2d5a27')
        center_scroll_frame.grid(row=2, column=0, sticky='nsew', padx=10, pady=10)
        center_scroll_frame.grid_rowconfigure(0, weight=1)
        center_scroll_frame.grid_columnconfigure(0, weight=1)
        
        self.center_cards = tk.Frame(center_scroll_frame, bg='#2d5a27')
        self.center_cards.grid(row=0, column=0)

        # AI Player 3 (right)
        right_frame = tk.Frame(middle_container, bg='#1a5f4a', bd=2, relief='raised')
        right_frame.grid(row=0, column=2, sticky='nsew', padx=(5, 0))
        tk.Label(right_frame, text="AI Player 3", bg='#1a5f4a', fg='white', 
                font=self.player_font).pack(anchor='w', padx=5, pady=2)
        
        self.player4_cards = tk.Frame(right_frame, bg='#1a5f4a')
        self.player4_cards.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.player4_count = tk.Label(right_frame, text="13 cards", bg='#1a5f4a', fg='gold', 
                                    font=self.info_font)
        self.player4_count.pack(anchor='e', padx=5, pady=2)

        # Special Skills Area
        skills_container = tk.Frame(self.root, bg='#4a1a5f', bd=2, relief='raised')
        skills_container.grid(row=3, column=0, sticky='ew', padx=10, pady=2)
        skills_container.grid_columnconfigure(1, weight=1)
        
        tk.Label(skills_container, text="🌟 SPECIAL SKILLS", bg='#4a1a5f', fg='gold', 
                font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky='w', padx=10, pady=5)
        
        self.skills_info = tk.Label(skills_container, text="Next skill round in 4 rounds", 
                                   bg='#4a1a5f', fg='white', font=self.info_font)
        self.skills_info.grid(row=0, column=1, sticky='e', padx=10, pady=5)
        
        self.skills_frame = tk.Frame(skills_container, bg='#4a1a5f')
        self.skills_frame.grid(row=1, column=0, columnspan=2, sticky='ew', padx=10, pady=5)

        # Player cards area
        player_container = tk.Frame(self.root, bg='#1a5f4a', bd=2, relief='raised')
        player_container.grid(row=4, column=0, sticky='ew', padx=10, pady=5)
        player_container.grid_rowconfigure(1, weight=1)
        player_container.grid_columnconfigure(0, weight=1)
        
        player_header = tk.Frame(player_container, bg='#1a5f4a')
        player_header.grid(row=0, column=0, sticky='ew', padx=10, pady=5)
        player_header.grid_columnconfigure(1, weight=1)
        
        tk.Label(player_header, text="YOUR CARDS", bg='#1a5f4a', fg='gold', 
                font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky='w')
        
        self.player_skills_lbl = tk.Label(player_header, text="Skills: None", bg='#1a5f4a', fg='cyan', 
                                         font=self.info_font)
        self.player_skills_lbl.grid(row=0, column=1, sticky='e')
        
        # Scrollable canvas for player cards
        player_canvas = tk.Canvas(player_container, bg='#1a5f4a', height=120)
        player_canvas.grid(row=1, column=0, sticky='ew', padx=10, pady=5)
        
        player_scrollbar = ttk.Scrollbar(player_container, orient='horizontal', command=player_canvas.xview)
        player_scrollbar.grid(row=2, column=0, sticky='ew', padx=10)
        player_canvas.configure(xscrollcommand=player_scrollbar.set)
        
        self.hand_frame = tk.Frame(player_canvas, bg='#1a5f4a')
        player_canvas.create_window((0, 0), window=self.hand_frame, anchor='nw')
        
        player_canvas.bind('<Configure>', lambda e: self.update_scroll_region(player_canvas, self.hand_frame))
        self.hand_frame.bind('<Configure>', lambda e: self.update_scroll_region(player_canvas, self.hand_frame))

        # Controls
        ctrl_frame = tk.Frame(self.root, bg='#0d4f3c', height=60)
        ctrl_frame.grid(row=5, column=0, sticky='ew', padx=10, pady=5)
        ctrl_frame.grid_propagate(False)
        
        self.play_btn = tk.Button(ctrl_frame, text="PLAY", command=self.play, bg='#4CAF50', fg='white',
                                 font=self.info_font, padx=15, height=1)
        self.play_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.pass_btn = tk.Button(ctrl_frame, text="PASS", command=self.pass_turn, bg='#FF9800', fg='white',
                                 font=self.info_font, padx=15, height=1)
        self.pass_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.skill_btn = tk.Button(ctrl_frame, text="USE SKILL", command=self.show_skills_menu, 
                                  bg='#9C27B0', fg='white', font=self.info_font, padx=15, height=1)
        self.skill_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        tk.Button(ctrl_frame, text="NEW GAME", command=self.new_game, bg='#2196F3', fg='white',
                 font=self.info_font, padx=15, height=1).pack(side=tk.LEFT, padx=10, pady=10)
        
        tk.Button(ctrl_frame, text="HELP", command=self.show_help, bg='#607D8B', fg='white',
                 font=self.info_font, padx=15, height=1).pack(side=tk.RIGHT, padx=10, pady=10)

    def update_scroll_region(self, canvas, frame):
        canvas.configure(scrollregion=canvas.bbox("all"))
        
    def center_window(self, window):
            """Center a window on the screen"""
            window.update_idletasks()
            width = window.winfo_width()
            height = window.winfo_height()
            x = (window.winfo_screenwidth() // 2) - (width // 2)
            y = (window.winfo_screenheight() // 2) - (height // 2)
            window.geometry(f'+{x}+{y}')

    def show_help(self):
        help_text = """
🃏 BIG TWO - SPECIAL EDITION 🃏

Aturan Dasar:
• Permainan dimulai dengan pemain yang memiliki 3♠
• Kombinasi: single, pair, triple, straight, flush, full house, four of a kind, straight flush
• Pemain pertama yang menghabiskan kartu menang

🌟 SPECIAL SKILLS (Setiap 4 putaran):
🎯 Sniper - Paksa lawan buang kartu tertinggi
🛡️ Shield - Lindungi dari efek negatif
👁️ Peek - Lihat kartu lawan
🔄 Swap - Tukar 2 kartu dengan lawan
⏭️ Skip - Lewati giliran lawan
🎲 Chaos - Semua pemain bertukar kartu
💎 Draw Lucky - Ambil kartu terendah dari deck
🃏 Wild Play - Mainkan kartu apapun (bypass aturan)
        """
        messagebox.showinfo("Bantuan", help_text)

    def new_game(self):
        self.over = False
        self.is_first_round = True
        self.first_play_made = False
        self.starter_index = None
        self.round_count = 0
        self.skill_phase = False
        self.available_skills = []
        self.pending_skill = None
        self.wild_play_active = False
        self.current, self.last_cards, self.last_type, self.last_val, self.pass_count, self.selected = 0, [], None, 0, 0, []
        
        self.deck = self.logic.create_deck()
        
        for p in self.players:
            p.cards.clear()
            p.special_skills.clear()
            p.shield_active = False
            p.skip_next_turn = False
        
        for _ in range(13):
            for p in self.players:
                if self.deck:
                    p.add_card(self.deck.pop())
        
        for p in self.players:
            p.sort_cards()
        
        # Find player with 3♠
        for i, p in enumerate(self.players):
            if any(c.value == '3' and c.suit == '♠' for c in p.cards):
                self.current = i
                self.starter_index = i
                break
        
        self.update()
        
        if self.current != 0:
            self.root.after(1000, self.ai_play)

    def check_skill_round(self):
            """Check if it's time for a skill round"""
            # Pastikan game sudah dimulai
            if not self.first_play_made:
                return
            
            # Hitung round dengan benar
            skill_round = (self.round_count % 4 == 0) and (self.round_count > 0)
            
            if skill_round and not self.skill_phase:
                self.skill_phase = True
                
                # Ambil 4 skill secara acak
                selected_skills = random.sample(self.logic.special_skills, 4)
                
                # Berikan satu skill acak untuk setiap pemain
                for i, player in enumerate(self.players):
                    if selected_skills:
                        skill = random.choice(selected_skills)
                        player.add_skill(skill)
                        selected_skills.remove(skill)
                        
                        # Tampilkan pesan untuk pemain manusia
                        if i == 0:
                            messagebox.showinfo("Skill Acquired!", 
                                            f"You have acquired: {skill.name}\n\n{skill.description}")
                
                # Reset status
                self.skill_phase = False
                self.update()

    def show_skills_menu(self):
        """Show available skills for the human player"""
        if not self.players[0].special_skills:
            messagebox.showinfo("No Skills", "You don't have any special skills yet!")
            return
        
        skills_window = tk.Toplevel(self.root)
        skills_window.title("🌟 Your Special Skills")
        skills_window.geometry("600x400")
        skills_window.configure(bg='#2d1a3f')
        skills_window.grab_set()
        skills_window.transient(self.root)
        
        # Center window
        skills_window.update_idletasks()
        x = (skills_window.winfo_screenwidth() // 2) - (skills_window.winfo_reqwidth() // 2)
        y = (skills_window.winfo_screenheight() // 2) - (skills_window.winfo_reqheight() // 2)
        skills_window.geometry(f"+{x}+{y}")
        
        tk.Label(skills_window, text="🌟 SELECT SKILL TO USE 🌟", 
                bg='#2d1a3f', fg='gold', font=('Arial', 16, 'bold')).pack(pady=20)
        
        # Skills list
        skills_frame = tk.Frame(skills_window, bg='#2d1a3f')
        skills_frame.pack(expand=True, fill='both', padx=20, pady=10)
        
        for i, skill in enumerate(self.players[0].special_skills):
            skill_frame = tk.Frame(skills_frame, bg='#4a1a5f', bd=2, relief='raised', padx=15, pady=10)
            skill_frame.pack(fill='x', pady=5)
            
            tk.Label(skill_frame, text=skill.name, bg='#4a1a5f', fg='gold', 
                    font=('Arial', 12, 'bold')).pack(anchor='w')
            tk.Label(skill_frame, text=skill.description, bg='#4a1a5f', fg='white', 
                    font=('Arial', 10), wraplength=500).pack(anchor='w', pady=2)
            
            use_btn = tk.Button(skill_frame, text="USE SKILL", 
                               command=lambda s=skill: self.use_skill(s, skills_window),
                               bg='#9C27B0', fg='white', font=('Arial', 10, 'bold'))
            use_btn.pack(anchor='e', pady=5)
        
        # Cancel button
        tk.Button(skills_window, text="CANCEL", command=skills_window.destroy,
                 bg='#FF5722', fg='white', font=('Arial', 12, 'bold')).pack(pady=20)

    def use_skill(self, skill, skills_window):
        """Use a special skill"""
        if not self.players[0].use_skill(skill):
            messagebox.showerror("Error", "You don't have this skill!")
            return
        
        skills_window.destroy()
        
        # Apply skill effect
        self.apply_skill_effect(skill, 0)  # Player 0 uses skill
        self.update()

    def select_target_player(self, skill, user_index):
        """Show dialog to select target player for targeted skills"""
        target_window = tk.Toplevel(self.root)
        target_window.title("Select Target")
        target_window.geometry("400x300")
        target_window.configure(bg='#2d1a3f')
        target_window.grab_set()
        target_window.transient(self.root)
        
        # Center window
        target_window.update_idletasks()
        x = (target_window.winfo_screenwidth() // 2) - (target_window.winfo_reqwidth() // 2)
        y = (target_window.winfo_screenheight() // 2) - (target_window.winfo_reqheight() // 2)
        target_window.geometry(f"+{x}+{y}")
        
        tk.Label(target_window, text=f"Select target for {skill.name}", 
                bg='#2d1a3f', fg='gold', font=('Arial', 14, 'bold')).pack(pady=20)
        
        for i, player in enumerate(self.players):
            if i != user_index:  # Can't target self
                btn_text = f"{player.name} ({len(player.cards)} cards)"
                if player.shield_active:
                    btn_text += " 🛡️"
                
                tk.Button(target_window, text=btn_text,
                         command=lambda target=i, w=target_window: self.execute_targeted_skill(skill, user_index, target, w),
                         bg='#4CAF50', fg='white', font=('Arial', 12), width=25).pack(pady=5)
        
        tk.Button(target_window, text="CANCEL", command=target_window.destroy,
                 bg='#FF5722', fg='white', font=('Arial', 12)).pack(pady=20)

    def execute_targeted_skill(self, skill, user_index, target_index, window=None):
        """Execute a targeted skill effect"""
        if window:
            window.destroy()
        
        target_player = self.players[target_index]
        
        # Check if target has shield
        if target_player.shield_active and skill.effect_type in ['force_discard', 'skip', 'swap']:
            target_player.shield_active = False  # Shield is consumed
            if user_index == 0:
                messagebox.showinfo("Shield!", f"{target_player.name}'s shield blocked the {skill.name}!")
            return
        
        if skill.effect_type == 'force_discard':
            if target_player.cards:
                highest_card = max(target_player.cards, key=lambda c: c.get_numeric_value())
                target_player.remove_cards([highest_card])
                if user_index == 0:
                    messagebox.showinfo("Sniper Hit!", f"Forced {target_player.name} to discard {highest_card}!")
        
        elif skill.effect_type == 'skip':
            target_player.skip_next_turn = True
            if user_index == 0:
                messagebox.showinfo("Skip!", f"{target_player.name} will skip their next turn!")
        
        elif skill.effect_type == 'swap':
            if len(target_player.cards) >= 2 and len(self.players[user_index].cards) >= 2:
                # Swap 2 random cards
                user_cards = random.sample(self.players[user_index].cards, 2)
                target_cards = random.sample(target_player.cards, 2)
                
                self.players[user_index].remove_cards(user_cards)
                target_player.remove_cards(target_cards)
                
                for card in target_cards:
                    self.players[user_index].add_card(card)
                for card in user_cards:
                    target_player.add_card(card)
                
                self.players[user_index].sort_cards()
                target_player.sort_cards()
                
                if user_index == 0:
                    messagebox.showinfo("Swap!", f"Swapped 2 cards with {target_player.name}!")
        
        elif skill.effect_type == 'peek':
            if user_index == 0:  # Human player
                self.show_peek_window(target_player)
            # No message for AI

    def show_peek_window(self, target_player):
        """Show peeked cards to human player"""
        peek_window = tk.Toplevel(self.root)
        peek_window.title(f"👁️ Peeking at {target_player.name}'s Cards")
        peek_window.geometry("800x300")
        peek_window.configure(bg='#1a0d26')
        peek_window.grab_set()
        peek_window.transient(self.root)
        
        # Center window
        peek_window.update_idletasks()
        x = (peek_window.winfo_screenwidth() // 2) - (peek_window.winfo_reqwidth() // 2)
        y = (peek_window.winfo_screenheight() // 2) - (peek_window.winfo_reqheight() // 2)
        peek_window.geometry(f"+{x}+{y}")
        
        tk.Label(peek_window, text=f"👁️ {target_player.name}'s Cards 👁️", 
                bg='#1a0d26', fg='gold', font=('Arial', 16, 'bold')).pack(pady=20)
        
        # Cards frame
        cards_frame = tk.Frame(peek_window, bg='#1a0d26')
        cards_frame.pack(expand=True, fill='both', padx=20, pady=10)
        
        # Display cards
        for i, card in enumerate(target_player.cards):
            card_btn = tk.Button(cards_frame, text=str(card), bg='white', fg='black',
                                font=self.card_font, width=6, height=3, bd=2, relief='raised')
            card_btn.grid(row=0, column=i, padx=2, pady=5)
        
        tk.Button(peek_window, text="CLOSE", command=peek_window.destroy,
                 bg='#FF5722', fg='white', font=('Arial', 12, 'bold')).pack(pady=20)

    def apply_skill_effect(self, skill, user_index):
        """Apply the effect of a special skill"""
        if skill.effect_type in ['force_discard', 'skip', 'swap', 'peek']:
            if user_index == 0:  # Human player
                self.select_target_player(skill, user_index)
            else:  # AI player
                # AI selects random target
                available_targets = [i for i in range(len(self.players)) if i != user_index]
                if available_targets:
                    target_index = random.choice(available_targets)
                    self.execute_targeted_skill(skill, user_index, target_index)
        
        elif skill.effect_type == 'shield':
            self.players[user_index].shield_active = True
            if user_index == 0:
                messagebox.showinfo("Shield Up!", "You are now protected from negative effects!")
        
        elif skill.effect_type == 'chaos':
            # All players pass 1 card to next player
            if all(len(p.cards) > 0 for p in self.players):
                cards_to_pass = []
                for player in self.players:
                    card_to_pass = random.choice(player.cards)
                    cards_to_pass.append(card_to_pass)
                    player.remove_cards([card_to_pass])
                
                # Pass cards to next player
                for i, card in enumerate(cards_to_pass):
                    next_player_index = (i + 1) % len(self.players)
                    self.players[next_player_index].add_card(card)
                
                for player in self.players:
                    player.sort_cards()
                
                if user_index == 0:
                    messagebox.showinfo("Chaos!", "All players passed 1 card to the next player!")
                else:
                    # Untuk AI, update tampilan sebelum melanjutkan
                    self.update()
                    self.root.after(2000, self.next_turn)
        
        elif skill.effect_type == 'draw_lucky':
            if self.deck:
                # Find the lowest card in deck
                lowest_card = min(self.deck, key=lambda c: c.get_numeric_value())
                self.deck.remove(lowest_card)
                self.players[user_index].add_card(lowest_card)
                self.players[user_index].sort_cards()
                
                if user_index == 0:
                    messagebox.showinfo("Lucky Draw!", f"You drew the lucky card: {lowest_card}!")
        elif skill.effect_type == 'wild_play':
            if user_index == 0:
                self.wild_play_active = True
                messagebox.showinfo("Wild Play!", "You can now play any card combination, ignoring normal rules!")
            else:
                # AI uses wild play immediately
                self.ai_wild_play(user_index)
                # Beri jeda sebelum melanjutkan
                self.root.after(2000, self.next_turn)

    def ai_wild_play(self, ai_index):
        """AI player uses wild play skill"""
        ai_player = self.players[ai_index]
        if ai_player.cards:
            # AI plays their highest single card or best combination
            if len(ai_player.cards) >= 5:
                # Coba kombinasi 5 kartu
                valid_play = self.ai_find_best_play(ai_player.cards, wild_play=True)
            elif len(ai_player.cards) >= 3:
                # Coba triple
                valid_play = self.ai_find_triple(ai_player.cards)
            else:
                # Mainkan kartu tunggal tertinggi
                valid_play = [max(ai_player.cards, key=lambda c: c.get_numeric_value())]
            
            if valid_play:
                ai_player.remove_cards(valid_play)
                self.last_cards = valid_play[:]
                combo_type, combo_val = self.logic.get_combo_type(valid_play)
                self.last_type = combo_type
                self.last_val = combo_val
                self.pass_count = 0
                
                # FIX: Check win condition
                if not ai_player.cards:
                    self.game_over(ai_index)
                    return

    def ai_find_triple(self, cards):
        """Find a triple combination"""
        value_counts = Counter(card.value for card in cards)
        for value, count in value_counts.items():
            if count >= 3:
                return [card for card in cards if card.value == value][:3]
        return None

    def play(self):
        if self.over or self.current != 0:
            return
        
        if not self.selected:
            messagebox.showwarning("No Cards", "Please select cards to play!")
            return
        
        # Check if it's a valid play
        is_valid = self.logic.is_valid_play(
            self.selected, self.last_cards, self.last_type, self.last_val, 
            self.is_first_round, self.wild_play_active
        )
        
        if not is_valid:
            if self.is_first_round:
                messagebox.showwarning("Invalid", "First play must include 3♠!")
            else:
                messagebox.showwarning("Invalid", "Invalid combination or too weak!")
            return
        
        # Play the cards
        self.players[0].remove_cards(self.selected)
        self.last_cards = self.selected[:]
        combo_type, combo_val = self.logic.get_combo_type(self.selected)
        self.last_type = combo_type
        self.last_val = combo_val
        self.pass_count = 0
        self.selected = []
        # FIX: Reset wild play after use
        self.wild_play_active = False
        
        if self.is_first_round:
            self.is_first_round = False
            self.first_play_made = True
        
        # Check win condition
        if not self.players[0].cards:
            self.game_over(0)
            return
        
        self.next_turn()

    def pass_turn(self):
        if self.over or self.current != 0:
            return
        
        self.pass_count += 1
        
        # After 3 passes, clear the table
        if self.pass_count >= 3:
            self.last_cards = []
            self.last_type = None
            self.last_val = 0
            self.pass_count = 0
            self.round_count += 1
            self.check_skill_round()
        
        self.next_turn()

    def next_turn(self):
        self.current = (self.current + 1) % 4
        
        # FIX: Only increment round count when a full rotation is completed
        if self.current == self.starter_index and not self.is_first_round:
            self.round_count += 1
            self.check_skill_round()
        
        # Skip players who are marked to skip
        if self.players[self.current].skip_next_turn:
            self.players[self.current].skip_next_turn = False
            self.pass_count += 1
            if self.pass_count >= 3:
                self.last_cards = []
                self.last_type = None
                self.last_val = 0
                self.pass_count = 0
                # Increment round count only when passes clear the table
                self.round_count += 1
                self.check_skill_round()
            self.next_turn()
            return
        
        self.update()
        
        if self.current != 0:
            self.root.after(1500, self.ai_play)

    def ai_play(self):
        if self.over or self.current == 0:
            return
        
        ai_player = self.players[self.current]
        
        # Prioritize using skills (60% chance)
        if ai_player.special_skills and random.random() < 0.6:
            skill = random.choice(ai_player.special_skills)
            if ai_player.use_skill(skill):
                self.apply_skill_effect(skill, self.current)
                self.update()
                # FIX: Beri waktu untuk efek skill terlihat
                self.root.after(2000, self.ai_continue)
                return
        
        # Continue with normal play
        self.ai_continue()
        
    def ai_continue(self):
        if self.over or self.current == 0:
            return
        
        ai_player = self.players[self.current]
        
        # Find valid play
        valid_play = self.ai_find_best_play(ai_player.cards)
        
        if valid_play:
            ai_player.remove_cards(valid_play)
            self.last_cards = valid_play[:]
            combo_type, combo_val = self.logic.get_combo_type(valid_play)
            self.last_type = combo_type
            self.last_val = combo_val
            self.pass_count = 0
            
            if self.is_first_round:
                self.is_first_round = False
                self.first_play_made = True
            
            # Check win condition
            if not ai_player.cards:
                self.game_over(self.current)
                return
        else:
            # AI passes
            self.pass_count += 1
            if self.pass_count >= 3:
                self.last_cards = []
                self.last_type = None
                self.last_val = 0
                self.pass_count = 0
                self.round_count += 1
                self.check_skill_round()
        
        self.next_turn()
    


    def ai_find_best_play(self, cards, wild_play=False):
        """Find the best play for AI with enhanced strategy"""
        if not cards:
            return None
        
        # Try to find valid combinations
        valid_plays = []
        
        # 1. Singles
        for card in cards:
            if self.logic.is_valid_play([card], self.last_cards, self.last_type, self.last_val, self.is_first_round, wild_play):
                valid_plays.append([card])
        
        # 2. Pairs
        for i in range(len(cards)):
            for j in range(i + 1, len(cards)):
                if cards[i].value == cards[j].value:
                    combo = [cards[i], cards[j]]
                    if self.logic.is_valid_play(combo, self.last_cards, self.last_type, self.last_val, self.is_first_round, wild_play):
                        valid_plays.append(combo)
        
        # 3. Triples
        value_counts = Counter(card.value for card in cards)
        for value, count in value_counts.items():
            if count >= 3:
                triple_cards = [card for card in cards if card.value == value][:3]
                if self.logic.is_valid_play(triple_cards, self.last_cards, self.last_type, self.last_val, self.is_first_round, wild_play):
                    valid_plays.append(triple_cards)
        
        # 4. Five-card combinations
        if len(cards) >= 5:
            # Generate all possible 5-card combinations
            from itertools import combinations
            five_card_combos = list(combinations(cards, 5))
            
            for combo in five_card_combos:
                combo_list = list(combo)
                combo_type, combo_val = self.logic.get_combo_type(combo_list)
                if combo_type and self.logic.is_valid_play(combo_list, self.last_cards, self.last_type, self.last_val, self.is_first_round, wild_play):
                    valid_plays.append(combo_list)
        
        # If no valid plays found
        if not valid_plays:
            return None
        
        # Strategy: Prefer to play more cards to reduce hand size
        valid_plays.sort(key=lambda play: len(play), reverse=True)
        
        # Among plays with same number of cards, prefer lower value cards
        best_play = valid_plays[0]
        same_length_plays = [play for play in valid_plays if len(play) == len(best_play)]
        
        if len(same_length_plays) > 1:
            # Prefer plays with lower total value
            same_length_plays.sort(key=lambda play: sum(c.get_numeric_value() for c in play))
            best_play = same_length_plays[0]
        
        return best_play

    def game_over(self, winner_index):
        self.over = True
        winner_name = self.players[winner_index].name
        
        # Calculate scores based on remaining cards
        scores = []
        for i, player in enumerate(self.players):
            score = sum(card.get_numeric_value() for card in player.cards)
            scores.append((player.name, score, len(player.cards)))
        
        # Create game over window
        game_over_window = tk.Toplevel(self.root)
        game_over_window.title("🎉 Game Over!")
        game_over_window.geometry("500x400")
        game_over_window.configure(bg='#1a0d26')
        game_over_window.grab_set()
        game_over_window.transient(self.root)
        
        # Center window
        game_over_window.update_idletasks()
        x = (game_over_window.winfo_screenwidth() // 2) - (game_over_window.winfo_reqwidth() // 2)
        y = (game_over_window.winfo_screenheight() // 2) - (game_over_window.winfo_reqheight() // 2)
        game_over_window.geometry(f"+{x}+{y}")
        
        # Winner announcement
        tk.Label(game_over_window, text="🎉 GAME OVER! 🎉", 
                bg='#1a0d26', fg='gold', font=('Arial', 20, 'bold')).pack(pady=20)
        
        tk.Label(game_over_window, text=f"🏆 WINNER: {winner_name} 🏆", 
                bg='#1a0d26', fg='gold', font=('Arial', 16, 'bold')).pack(pady=10)
        
        # Scores
        tk.Label(game_over_window, text="Final Scores:", 
                bg='#1a0d26', fg='white', font=('Arial', 14, 'bold')).pack(pady=10)
        
        scores_frame = tk.Frame(game_over_window, bg='#1a0d26')
        scores_frame.pack(pady=10)
        
        for name, score, cards_left in scores:
            color = 'gold' if name == winner_name else 'white'
            tk.Label(scores_frame, text=f"{name}: {cards_left} cards left (Score: {score})", 
                    bg='#1a0d26', fg=color, font=('Arial', 12)).pack()
        
        # Buttons
        button_frame = tk.Frame(game_over_window, bg='#1a0d26')
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="NEW GAME", command=lambda: [game_over_window.destroy(), self.new_game()],
                 bg='#4CAF50', fg='white', font=('Arial', 12, 'bold')).pack(side=tk.LEFT, padx=10)
        
        tk.Button(button_frame, text="QUIT", command=self.root.quit,
                 bg='#FF5722', fg='white', font=('Arial', 12, 'bold')).pack(side=tk.LEFT, padx=10)

    def toggle_selection(self, card):
        if card in self.selected:
            self.selected.remove(card)
        else:
            self.selected.append(card)
        self.update_hand()

    def update_hand(self):
        # Clear existing widgets
        for widget in self.hand_frame.winfo_children():
            widget.destroy()
        
        # Sort cards
        self.players[0].sort_cards()
        
        # Display cards
        for i, card in enumerate(self.players[0].cards):
            is_selected = card in self.selected
            bg_color = '#FFD700' if is_selected else 'white'
            text_color = 'black'
            
            # Determine card color
            if card.suit in ['♥', '♦']:
                text_color = 'red'
            
            card_btn = tk.Button(self.hand_frame, text=str(card), bg=bg_color, fg=text_color,
                                font=self.card_font, width=6, height=3, bd=2, relief='raised',
                                command=lambda c=card: self.toggle_selection(c))
            card_btn.grid(row=0, column=i, padx=2, pady=2)

    def display_ai_cards(self, player_index, frame, count_label):
        # Clear existing widgets
        for widget in frame.winfo_children():
            widget.destroy()
        
        player = self.players[player_index]
        card_count = len(player.cards)
        
        # Update count label
        count_label.config(text=f"{card_count} cards")
        
        # Show card backs for AI players
        cards_to_show = min(card_count, 10)  # Show max 10 card backs
        
        for i in range(cards_to_show):
            card_back = tk.Label(frame, text="🂠", bg='#4169E1', fg='white',
                            font=('Arial', 12), width=3, height=2, bd=1, relief='raised')
            
            # FIX: Proper card display for different positions
            if player_index == 1:  # Top player (horizontal)
                card_back.grid(row=0, column=i, padx=1)
            elif player_index == 2:  # Left player (vertical)
                card_back.grid(row=i, column=0, pady=1)
            else:  # Right player (vertical)
                card_back.grid(row=i, column=0, pady=1)
        
        # Show skills indicator - only for human player
        # For AI players, we don't show any skill indicators
        if player_index == 0 and player.special_skills:
            skills_indicator = tk.Label(frame, text="🌟", bg='#4a1a5f', fg='gold',
                                    font=('Arial', 14))
            if player_index == 1:
                skills_indicator.grid(row=1, column=0, columnspan=cards_to_show)
            else:
                skills_indicator.grid(row=cards_to_show, column=0)

    def display_center_cards(self):
        # Clear existing widgets
        for widget in self.center_cards.winfo_children():
            widget.destroy()
        
        if not self.last_cards:
            tk.Label(self.center_cards, text="No cards played yet", bg='#2d5a27', fg='white',
                    font=self.info_font).pack()
            return
        
        # Display last played cards
        cards_frame = tk.Frame(self.center_cards, bg='#2d5a27')
        cards_frame.pack()
        
        for i, card in enumerate(self.last_cards):
            text_color = 'red' if card.suit in ['♥', '♦'] else 'black'
            
            card_lbl = tk.Label(cards_frame, text=str(card), bg='white', fg=text_color,
                               font=self.card_font, width=6, height=3, bd=2, relief='raised')
            card_lbl.grid(row=0, column=i, padx=2, pady=2)

    def update(self):
        if self.over:
            return
        
        # Update current player indicator
        current_player_name = self.players[self.current].name
        if self.players[self.current].skip_next_turn:
            current_player_name += " (Will Skip)"
        self.cur_lbl.config(text=f"Current: {current_player_name}")
        
        # Update combo information
        if self.last_cards:
            combo_type, combo_val = self.logic.get_combo_type(self.last_cards)
            combo_text = f"Last: {combo_type.replace('_', ' ').title()} ({combo_val})"
            cards_text = " ".join(str(c) for c in self.last_cards)
            self.combo_lbl.config(text=combo_text)
            self.last_lbl.config(text=cards_text)
        else:
            self.combo_lbl.config(text="Combo: Free play")
            self.last_lbl.config(text="Any valid combination")
        
        # Update pass count
        self.pass_lbl.config(text=f"Pass Count: {self.pass_count}")
        
        # Update round count
        self.round_lbl.config(text=f"Round: {self.round_count + 1}")
        
        # Update skills info
        rounds_until_skill = 4 - ((self.round_count + 1) % 4)
        if rounds_until_skill == 4:
            rounds_until_skill = 0
        
        if self.skill_phase:
            self.skills_info.config(text="🌟 SKILL ROUND ACTIVE! 🌟")
        elif rounds_until_skill == 0:
            self.skills_info.config(text="Next skill round NOW!")
        else:
            self.skills_info.config(text=f"Next skill round in {rounds_until_skill} rounds")
        
        # Update player skills display
        player_skills = self.players[0].special_skills
        if player_skills:
            skills_text = "Skills: " + ", ".join(skill.name for skill in player_skills)
            if self.players[0].shield_active:
                skills_text += " | 🛡️ Shield Active"
        else:
            skills_text = "Skills: None"
            if self.players[0].shield_active:
                skills_text = "Skills: None | 🛡️ Shield Active"
        
        self.player_skills_lbl.config(text=skills_text)
        
        # Update button states
        if self.current == 0 and not self.over:
            self.play_btn.config(state='normal')
            self.pass_btn.config(state='normal')
            if self.players[0].special_skills:
                self.skill_btn.config(state='normal')
            else:
                self.skill_btn.config(state='disabled')
        else:
            self.play_btn.config(state='disabled')
            self.pass_btn.config(state='disabled')
            self.skill_btn.config(state='disabled')
        
        # Update all displays
        self.update_hand()
        self.display_center_cards()
        self.display_ai_cards(1, self.player2_cards, self.player2_count)
        self.display_ai_cards(2, self.player3_cards, self.player3_count)
        self.display_ai_cards(3, self.player4_cards, self.player4_count)
        
        # Update skills display
        self.update_skills_display()
    
    def update_skills_display(self):
        """Update the skills display area - now hides AI skills"""
        # Clear existing widgets
        for widget in self.skills_frame.winfo_children():
            widget.destroy()
        
        # Show skills only for human player and hide for AI players
        for i, player in enumerate(self.players):
            if player.special_skills or player.shield_active:
                player_frame = tk.Frame(self.skills_frame, bg='#4a1a5f', bd=1, relief='raised')
                player_frame.pack(side=tk.LEFT, padx=5, pady=2, fill='x')
                
                # Player name
                tk.Label(player_frame, text=player.name, bg='#4a1a5f', fg='gold', 
                        font=('Arial', 9, 'bold')).pack()
                
                # Skills - only show for human player
                if player.special_skills:
                    if i == 0:  # Human player
                        for skill in player.special_skills:
                            tk.Label(player_frame, text=skill.name, bg='#4a1a5f', fg='white', 
                                    font=('Arial', 8)).pack()
                    else:  # AI players - show hidden indicator
                        tk.Label(player_frame, text="🔒 Skill Tersembunyi", bg='#4a1a5f', fg='#aaaaaa', 
                                font=('Arial', 8)).pack()
                
                # Shield status - show for all
                if player.shield_active:
                    tk.Label(player_frame, text="🛡️ Shield", bg='#4a1a5f', fg='cyan', 
                            font=('Arial', 8)).pack()
    
    def show_game_rules(self):
        """Show detailed game rules"""
        rules_window = tk.Toplevel(self.root)
        rules_window.title("📖 Big Two Rules")
        rules_window.geometry("700x600")
        rules_window.configure(bg='#1a0d26')
        rules_window.grab_set()
        rules_window.transient(self.root)
        self.center_window(rules_window)
        
        # Create scrollable text
        text_frame = tk.Frame(rules_window, bg='#1a0d26')
        text_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(text_frame, bg='#2d1a3f', fg='white', font=('Arial', 11),
                             yscrollcommand=scrollbar.set, wrap=tk.WORD)
        text_widget.pack(side=tk.LEFT, fill='both', expand=True)
        scrollbar.config(command=text_widget.yview)
        
        rules_text = """
🃏 BIG TWO - SPECIAL EDITION RULES 🃏

BASIC RULES:
• 4 players, 13 cards each
• Card order: 3 < 4 < 5 < 6 < 7 < 8 < 9 < 10 < J < Q < K < A < 2
• Suit order: ♠ < ♣ < ♦ < ♥
• First player must have 3♠ and include it in first play
• Players must play higher combinations of the same type
• Pass 3 times to clear the table and start new round

COMBINATIONS:
• Single Card: Any card
• Pair: Two cards of same rank
• Triple: Three cards of same rank
• Straight: 5 consecutive cards (A-2-3-4-5 is valid)
• Flush: 5 cards of same suit
• Full House: 3 of a kind + pair
• Four of a Kind: 4 cards of same rank + 1 card
• Straight Flush: 5 consecutive cards of same suit

SPECIAL SKILLS (Every 4 rounds):
🎯 Sniper: Force target player to discard their highest card
🛡️ Shield: Protect yourself from next negative effect
👁️ Peek: View another player's cards
🔄 Swap: Swap 2 random cards with target player
⏭️ Skip: Skip target player's next turn
🎲 Chaos: All players pass 1 card to next player
💎 Draw Lucky: Draw the lowest card from deck
🃏 Wild Play: Play any card regardless of rules

WINNING:
• First player to play all cards wins
• Score = sum of remaining cards' values
• Lower score is better

STRATEGY TIPS:
• Save your 2s and Aces for important plays
• Use skills strategically
• Watch other players' card counts
• Try to go out with low cards
        """
        
        text_widget.insert('1.0', rules_text)
        text_widget.config(state='disabled')
        
        tk.Button(rules_window, text="CLOSE", command=rules_window.destroy,
                 bg='#FF5722', fg='white', font=('Arial', 12, 'bold')).pack(pady=10)
    
    def save_game_state(self):
        """Save current game state (placeholder for future implementation)"""
        messagebox.showinfo("Save Game", "Game save feature coming soon!")
    
    def load_game_state(self):
        """Load saved game state (placeholder for future implementation)"""
        messagebox.showinfo("Load Game", "Game load feature coming soon!")
    
    def show_statistics(self):
        """Show game statistics (placeholder for future implementation)"""
        messagebox.showinfo("Statistics", "Statistics feature coming soon!")
    
    def toggle_sound(self):
        """Toggle sound effects (placeholder for future implementation)"""
        messagebox.showinfo("Sound", "Sound toggle feature coming soon!")
    
    def change_theme(self):
        """Change game theme (placeholder for future implementation)"""
        messagebox.showinfo("Theme", "Theme selection feature coming soon!")
    
    def show_about(self):
        """Show about dialog"""
        about_window = tk.Toplevel(self.root)
        about_window.title("About Big Two")
        about_window.geometry("400x300")
        about_window.configure(bg='#1a0d26')
        about_window.grab_set()
        about_window.transient(self.root)
        self.center_window(about_window)
        
        tk.Label(about_window, text="🃏 BIG TWO", bg='#1a0d26', fg='gold', 
                font=('Arial', 20, 'bold')).pack(pady=20)
        
        tk.Label(about_window, text="SPECIAL EDITION", bg='#1a0d26', fg='white', 
                font=('Arial', 14, 'bold')).pack()
        
        tk.Label(about_window, text="Version 1.0", bg='#1a0d26', fg='white', 
                font=('Arial', 12)).pack(pady=10)
        
        tk.Label(about_window, text="A classic card game with special skills\nand enhanced gameplay features.", 
                bg='#1a0d26', fg='white', font=('Arial', 11), justify='center').pack(pady=10)
        
        tk.Label(about_window, text="Created with Python & Tkinter", bg='#1a0d26', fg='cyan', 
                font=('Arial', 10, 'italic')).pack(pady=10)
        
        tk.Button(about_window, text="CLOSE", command=about_window.destroy,
                 bg='#4CAF50', fg='white', font=('Arial', 12, 'bold')).pack(pady=20)
    
    def on_window_closing(self):
        """Handle window closing event"""
        if messagebox.askokcancel("Quit", "Are you sure you want to quit the game?"):
            self.root.destroy()
    
    def setup_menu(self):
        """Setup the menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Game menu
        game_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Game", menu=game_menu)
        game_menu.add_command(label="New Game", command=self.new_game)
        game_menu.add_separator()
        game_menu.add_command(label="Save Game", command=self.save_game_state)
        game_menu.add_command(label="Load Game", command=self.load_game_state)
        game_menu.add_separator()
        game_menu.add_command(label="Exit", command=self.on_window_closing)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Statistics", command=self.show_statistics)
        view_menu.add_command(label="Change Theme", command=self.change_theme)
        
        # Options menu
        options_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Options", menu=options_menu)
        options_menu.add_command(label="Toggle Sound", command=self.toggle_sound)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Game Rules", command=self.show_game_rules)
        help_menu.add_command(label="How to Play", command=self.show_help)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)
    
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts"""
        self.root.bind('<Return>', lambda e: self.play() if self.current == 0 else None)
        self.root.bind('<space>', lambda e: self.pass_turn() if self.current == 0 else None)
        self.root.bind('<Control-n>', lambda e: self.new_game())
        self.root.bind('<F1>', lambda e: self.show_help())
        self.root.bind('<Control-q>', lambda e: self.on_window_closing())
        
        # Card selection shortcuts (1-9, 0 for 10th card)
        for i in range(10):
            key = str(i) if i > 0 else '0'
            self.root.bind(key, lambda e, idx=i: self.select_card_by_index(idx))
    
    def select_card_by_index(self, index):
        """Select card by keyboard shortcut"""
        if self.current == 0 and not self.over:
            player_cards = self.players[0].cards
            if 0 <= index < len(player_cards):
                card = player_cards[index]
                self.toggle_selection(card)
    
    def enhanced_ai_strategy(self, ai_index):
        """Enhanced AI strategy with skill usage"""
        ai_player = self.players[ai_index]
        
        # Analyze game state
        total_cards_left = sum(len(p.cards) for p in self.players)
        avg_cards = total_cards_left / 4
        ai_card_count = len(ai_player.cards)
        
        # Determine AI strategy based on position
        if ai_card_count <= 3:
            # Aggressive - try to win
            strategy = "aggressive"
        elif ai_card_count > avg_cards + 2:
            # Defensive - try to catch up
            strategy = "defensive"
        else:
            # Balanced
            strategy = "balanced"
        
        # Use skills based on strategy
        if ai_player.special_skills:
            for skill in ai_player.special_skills[:]:  # Copy list to avoid modification during iteration
                if self.should_ai_use_skill(skill, ai_index, strategy):
                    ai_player.use_skill(skill)
                    self.apply_skill_effect(skill, ai_index)
                    self.update()
                    return True
        
        return False
    
    def should_ai_use_skill(self, skill, ai_index, strategy):
        """Determine if AI should use a specific skill"""
        ai_player = self.players[ai_index]
        
        # Basic probability based on strategy
        if strategy == "aggressive":
            base_prob = 0.3
        elif strategy == "defensive":
            base_prob = 0.4
        else:
            base_prob = 0.2
        
        # Skill-specific logic
        if skill.effect_type == "shield":
            # Use shield if vulnerable (many cards)
            return len(ai_player.cards) > 8 and random.random() < base_prob
        
        elif skill.effect_type == "force_discard":
            # Use sniper against player with few cards
            min_cards = min(len(p.cards) for i, p in enumerate(self.players) if i != ai_index)
            return min_cards <= 5 and random.random() < base_prob
        
        elif skill.effect_type == "skip":
            # Use skip strategically
            return random.random() < base_prob * 0.7
        
        elif skill.effect_type == "wild_play":
            # Use wild play when stuck or to make aggressive play
            return len(ai_player.cards) <= 4 and random.random() < base_prob * 1.5
        
        else:
            # General usage
            return random.random() < base_prob

# Initialize and run the game
if __name__ == "__main__":
    try:
        game = BigTwoGame()
    except Exception as e:
        print(f"Error starting game: {e}")
        import traceback
        traceback.print_exc()