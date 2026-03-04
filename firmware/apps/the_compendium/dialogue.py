import cutscene


# The node type they all come from, contains data about whether the node should appear in menus, give the player items and so forth.
class ActionNode:
    def __init__(self, text, image, prerequisites, childnodes, menutext, given_item, removed_item):
        self.text = text
        self.image = image
        self.prerequisites = prerequisites
        self.childnodes = childnodes
        self.viable_child_nodes = []
        self.menutext = menutext
        self.given_item = given_item
        self.removed_item = removed_item

    def get_viable_children(self, player):
        self.viable_child_nodes.clear()
        for node in self.childnodes:
            if node is None:
                self.viable_child_nodes.append(node)
                continue
            node_data = dialogue_library[node]
            if set(node_data.prerequisites).issubset(set(player.inventory)):
                self.viable_child_nodes.append(node)

    def choose(self, choice):
        if len(self.viable_child_nodes) > choice:
            chosen_option = self.viable_child_nodes[choice]
            if chosen_option is None:
                return None
            return dialogue_library[chosen_option]
        return self

    def draw(self, player, font, ui_tex):
        self.get_viable_children(player)
        children = []
        for node in self.viable_child_nodes:
            if node is None:
                children.append("[Leave.]")
            else:
                node_data = dialogue_library[node]
                children.append(node_data.menutext)
        dialog = cutscene.DialogBox(self.image, self.text, cutscene.CutsceneLayout.img_left, font, children)
        dialog.draw(ui_tex)

    def __str__(self):
        return self.menutext

# A dialogue node also contains an ID so we can save that ID and come back to it to resume conversations after sleep
class DialogueNode(ActionNode):
    def __init__(self, id, text, image, prerequisites, childnodes, menutext, given_item, removed_item):
        super().__init__(text, image, prerequisites, childnodes, menutext, given_item, removed_item)
        self.id = id

# Contains information about the destination level and the player's start point and orientation in it.
class LevelSelectNode(ActionNode):
    def __init__(self, prerequisites, menutext, given_item, removed_item, level_id, entry_point, angle):
        super().__init__("", None, prerequisites, [], menutext, given_item, removed_item)
        self.level_id = level_id
        self.entry_point = entry_point
        self.angle = angle

# Just exists to tell the parser to go the end game.
class ExitNode(ActionNode):
    def __init__(self):
        super().__init__("", None, [], [], "[Leave The Compendium]", [], [])

    def draw(self, screen):
        screen.blit(screen, vec2(0, 0))

# Finally we have all of the dialogue lines and portrait images.
sb_portrait = image.load("assets/solderbeard.png")
mk_portrait = image.load("assets/monkey.png")
nj_portrait = image.load("assets/ninja.png")
rb_portrait = image.load("assets/robot.png")
crate_portrait = image.load("assets/crate_portrait.png")

dialogue_library = {
    "sb_greeting": DialogueNode("sb_greeting", "By the kraken, a visitor! 'Tis a while since we had one of those in these here parts.", sb_portrait, [], ["sb_whoyou", "sb_whatplace", "sb_ninja", "sb_comic", "sb_home", None], "", [], []),
    "sb_hub": DialogueNode("sb_hub", "Anyway, what else can I be doin' for ya, me young heartie?", sb_portrait, [], ["sb_whoyou", "sb_whatplace", "sb_ninja", "sb_comic", "sb_home", None], "[Continue]", [], []),
    "sb_whoyou": DialogueNode("sb_whoyou", "Cap'n Solderbeard, at your service. A more stalwart cove has never sailed the seven seas, if I do say so meself.", sb_portrait, [], ["sb_name"], "Who are you?", [], []),
    "sb_name": DialogueNode("sb_name", "Ah, the beard. Well ye see, I loves me tinkerin'. And 'tis difficult to be clean and neat with a solderin' iron on a movin' ship.", sb_portrait, [], ["sb_name2"], "That's... quite the name.", [], []),
    "sb_name2": DialogueNode("sb_name2", "And it conditions it wonderfully. Well, tins it. Sleek, shiny, and nigh on bulletproof.", sb_portrait, [], ["sb_hub"], "O...kay...", [], []),
    "sb_whatplace": DialogueNode("sb_whatplace", "Ah by the gods, where are me manners? Welcome to the Compendium.", sb_portrait, [], ["sb_whatplace2"], "What is this place?", [], []),
    "sb_whatplace2": DialogueNode("sb_whatplace2", "Aye, the Compendium. 'Tis our own little pocket of space time. Sealed away for many a year, known only to a select few foolhardy enough or bored enough to find us. Call it... a dimensional flat share.", sb_portrait, [], ["sb_hub"], "The Compendium?", [], []),
    "sb_ninja": DialogueNode("sb_ninja", "Oh, him? He's harmless. Well, for a ninja.", sb_portrait, ["nj_meet"], ["sb_ninja2"], "What's the deal with the ninja?", ["pocky"], []),
    "sb_ninja2": DialogueNode("sb_ninja2", "Ye just have to know how to handle him. He be a sucker for his favourite snack. Check yer inventory.", sb_portrait, [], ["sb_hub"], "He doesn't talk.", ["note_ninjasnack"], ["nj_meet"]),
    "sb_comic": DialogueNode("sb_comic", "Sorry, me young tar, I'm not much of a reader. Try the others.", sb_portrait, ["mk_quest"], ["sb_hub"], "Have you seen a comic book?", [], []),
    "sb_home": DialogueNode("sb_home", "Aye, that I can. I have me apparatus right here, but - ah, drat, no batteries. Can't do anything without them.", sb_portrait, ["nj_awake"], ["sb_hub", "sb_battery"], "Can you get me home?", [], []),
    "sb_battery": DialogueNode("sb_battery", "Perfect, me old sea dog! Alright, let's get ye out of there....", sb_portrait, ["battery"], ["exit"], "I've got a battery, here.", [], []),
    "mk_greeting": DialogueNode("mk_greeting", "Sup.", mk_portrait, [], ["mk_whoyou", "mk_whatplace", "mk_whytalk", "mk_ninja", "mk_accusation", "mk_present_comic", "mk_banana", None], "", [], []),
    "mk_hub": DialogueNode("mk_hub", "Anyway, yeah, what?", mk_portrait, [], ["mk_whoyou", "mk_whatplace", "mk_whytalk", "mk_ninja", "mk_accusation", "mk_present_comic", "mk_banana", None], "[Continue]", [], []),
    "mk_whoyou": DialogueNode("mk_whoyou", "What does it look like? I'm just a monkey. You know? Hairy, arboreal primate?", mk_portrait, [], ["mk_hub"], "Who are you?", ["unlock_mk_whytalk"], []),
    "mk_whytalk": DialogueNode("mk_whytalk", "Why are YOU talking? Specifically, why are you talking to ME? I never asked for it.", mk_portrait, ["unlock_mk_whytalk"], ["mk_getquest"], "Why are you talking?", [], ["unlock_mk_whytalk"]),
    "mk_whatplace": DialogueNode("mk_whatplace", "Just your typical subtropical forest. Y'know, trees, vines, bugs. There was a documentary crew here once, but I avoided them. Wasn't Attenborough, wasn't interested.", mk_portrait, [], ["mk_hub"], "What is this place?", [], []),
    "mk_getquest": DialogueNode("mk_getquest", "Wait, wait... can you do me a favour? I got some literature keeps me sane in here, I've misplaced it. Probably one of my roommates took it. Can ya ask around for me?", mk_portrait, [], ["mk_getquest2"], "Sorry, I'll go.", [], []),
    "mk_getquest2": DialogueNode("mk_getquest2", "The Adventures of Dora Daring, Space Barbarian, volume 3 issue 217. A fascinating post-maximalist deconstruction of the graphic panel art form. The others steal it. I think just to get on my nerves.", mk_portrait, [], ["mk_getquest3"], "What's the book?", [], []),
    "mk_getquest3": DialogueNode("mk_getquest3", "What do I look like, a gibbon? Too highfalutin' for them. Ninja guy once made a crack about something to do with fur loincloths and big rayguns, but yeah, pretty sure it's just to annoy me.", mk_portrait, [], ["mk_getquest4"], "You don't think they'd enjoy reading it?", [], []),
    "mk_getquest4": DialogueNode("mk_getquest4", "You're a pal.", mk_portrait, [], ["mk_hub"], "I'll find it.", ["mk_quest"], []),
    "mk_ninja": DialogueNode("mk_ninja", "Eeh, search me. Guy's like a sponge for stupid ideas, probably heard somewhere it's cool. S'definitely cooler than when he opens his mouth.", mk_portrait, ["nj_meet"], ["mk_hub"], "Why doesn't the ninja talk?", [], []),
    "mk_accusation": DialogueNode("mk_accusation", "Oh, that little - I swear, if I didn't have to clean it up I'd be in there right now flinging- never mind. I didn't take his damn scroll. The robot did. Needed it to patch a leak or something.", mk_portrait, ["unlock_mk_accusation"], ["mk_hub"], "D'you have the ninja's wall scroll?", ["note_robotpatch"], ["unlock_mk_accusation"]),
    "mk_present_comic": DialogueNode("mk_present_comic", "Nice work, kid. A classic of modern literature is safe once again.", mk_portrait, ["comic_book"], ["mk_present2"], "Here you go, one comic, slightly foxed.", [], ["comic_book"]),
    "mk_present2": DialogueNode("mk_present2", "You'll probably wanna get home, right? Yeah, old Solderbeard can help ya. Probably his experiments brought you here in the first place. Take this battery, he'll probably need it. Oh, and this.", mk_portrait, [], ["mk_hub"], "No worries.", ["battery", "banana"], []),
    "mk_banana": DialogueNode("mk_banana", "Banana AND a battery, don't forget. Yeah, I'm a monkey, it's kinda contractual. Besides, good for potassium.", mk_portrait, ["banana"], ["mk_hub"], "Why a banana?", [], []),
    "rb_greeting": DialogueNode("rb_greeting", "Greetings, human! Welcome to Spaceport Zeta, your gateway to the cosmos! I'm Lizzie, your customer service pal!", rb_portrait, [], ["rb_whoyou", "rb_whatplace", "rb_ninja", "rb_comic", "rb_scroll", "rb_swap", None], "", [], []),
    "rb_hub": DialogueNode("rb_hub", "How can I make your day even better today?", rb_portrait, [], ["rb_whoyou", "rb_whatplace", "rb_ninja", "rb_comic", "rb_scroll", "rb_swap", None], "[Continue]", [], []),
    "rb_whoyou": DialogueNode("rb_whoyou", "I'm Lizzie, your customer service pal! I'm here to make everything just super! [NO SUBSTITUTIONS EXCHANGES OR REFUNDS]", rb_portrait, [], ["rb_hub"], "Who are you?", [], []),
    "rb_whatplace": DialogueNode("rb_whatplace", "Why, you're at Space Station Zeta! Your Gateway To The Stars, for a low, low price! [SOME DESTINATIONS INCUR SURCHARGE]", rb_portrait, [], ["rb_rundown"], "What is this place?", [], []),
    "rb_rundown": DialogueNode("rb_rundown", "Our Station Maintenance Partners ensure that all systems are finely tuned! Any dust, dirt or decay you see is simply an imagining due to our low, low prices and oxygen levels!", rb_portrait, [], ["rb_rundown2"], "Looks a little run down...", [], []),
    "rb_rundown2": DialogueNode("rb_rundown2", "Medical Assistance Enforcers will be arriving shortly to treat your delusions, [INSERT HONOROFIC HERE]!", rb_portrait, [], ["rb_hub"], "Look around - it's falling apart!", [], ["unlock_rb_rundown"]),
    "rb_ninja": DialogueNode("rb_ninja", "[CUSTOMER ID NINJA] has not voiced a single complaint regarding our service! That puts him in the top [INFINITY] of our customers for satisfaction!", rb_portrait, ["nj_meet"], ["rb_hub"], "Why doesn't the ninja speak?", [], []),
    "rb_comic": DialogueNode("rb_comic", "I've seen all sorts of people book, friend! Comics, singers, radio stars - all the celebrities are booking through Space Station Zeta! [NOTE: SPACE STATION ZETA IS NOT ENDORSED BY ANY CELEBRITIES ABOVE LEVEL THREE]", rb_portrait, ["mk_quest"], ["rb_hub"], "Have you seen a comic book?", [], []),
    "rb_scroll": DialogueNode("rb_scroll", "Of course! Any customer can scroll down our-", rb_portrait, ["note_robotpatch"], ["rb_scroll2"], "I'm looking for a scroll.", [], []),
    "rb_scroll2": DialogueNode("rb_scroll2", "Of course, [INSERT HONORIFIC HERE]! That item was unfortunately required on company business, to alleviate an Unexpected Atmospheric Freedom Event!", rb_portrait, [], ["rb_scroll3"], "Wait - I mean the ninja's scroll. A wall scroll.", [], []),
    "rb_scroll3": DialogueNode("rb_scroll3", "Of course not! Not while that scroll is stuffed in there! If a replacement can be found, I would be glad to uncommandeer the customer's property! [FEES MAY APPLY]", rb_portrait, [], ["rb_hub"], "The station has a leak?", [], []),
    "rb_swap": DialogueNode("rb_swap", "Processing... Ah! A valued customer has come to plug the leak! Welcome, [CUSTOMER ID HATSUNE]! You will make a perfect plug!", rb_portrait, ["body_pillow"], ["rb_swap2"], "Okay, I got you something to swap out.", [], []),
    "rb_swap2": DialogueNode("rb_swap2", "Of course! Please take this complimentary wall scroll, [INSERT HONOROFIC HERE]! Space Station Zeta will remain vacuum tight, safe and secure for many rotations! [NOT EVEN AIR WILL ESCAPE]", rb_portrait, [], ["rb_hub"], "So I can have the scroll back?", ["wall_scroll", "meatloaf_recipe"], ["body_pillow", "note_robotpatch"]),
    "nj_greeting": DialogueNode("nj_greeting", "...", nj_portrait, [], ["nj_greeting2", "nj_greetinghub", None], "", [], []),
    "nj_greetinghub": DialogueNode("nj_greetinghub", "Well done, your powers are growing. Come, learn from your sensei.", nj_portrait, ["nj_awake"], ["nj_whoyou", "nj_whatplace", "nj_comic", "nj_swap", None], "I can still see you.", [], []),
    "nj_greeting2": DialogueNode("nj_greeting2", "....silent....I am the night....", nj_portrait, ["unlock_nj_hello"], ["nj_greeting3"], "Hello?", [], []),
    "nj_greeting3": DialogueNode("nj_greeting3", "[You've never seen someone put so much sweat into keeping still.]", nj_portrait, [], ["nj_awake", None], "Hellooo?", ["nj_meet"], []),
    "nj_awake": DialogueNode("nj_awake", "...I am- did you say Pocky? Damn! Hi.", nj_portrait, ["pocky"], ["nj_whoyou", "nj_whatplace", "nj_whatplace2", "nj_comic", "nj_swap", None], "I brought Pocky...", ["nj_awake"], ["unlock_nj_hello", "nj_meet", "note_ninjasnack"]),
    "nj_hub": DialogueNode("nj_hub", "Come, learn from your sensei.", nj_portrait, [], ["nj_whoyou", "nj_whatplace", "nj_whatplace2", "nj_comic", "nj_swap", None], "[Continue]", [], []),
    "nj_whoyou": DialogueNode("nj_whoyou", "I have no name. I am shadow... I am the night. Such questions are insulting to your daimyo.", nj_portrait, [], ["nj_whoyoureally"], "Who are you?", [], []),
    "nj_whoyoureally": DialogueNode("nj_whoyoureally", "No, wait! Alright, fine. It's Kevin.", nj_portrait, [], ["nj_hub"], "I can take the Pocky away again.", ["nj_name"], []),
    "nj_whatplace": DialogueNode("nj_whatplace", "The Temple of the Clouds... for untold ages this dojo has only trained the best in the arts of stealth, infiltration and stabbing.", nj_portrait, [], ["nj_hub"], "What is this place?", ["unlock_nj_whatplace2"], []),
    "nj_whatplace2": DialogueNode("nj_whatplace2", "Well, 1983. My uncle Jared set it up after his car wash business at the strip mall closed.", nj_portrait, ["unlock_nj_whatplace2", "nj_name"], ["nj_hub"], "So... untold ages, huh?", [], []),
    "nj_comic": DialogueNode("nj_comic", "NANI? No! Who told you that? Who- it would go against my code of honour! The honour of a ninja!", nj_portrait, ["mk_quest"], ["nj_comic2"], "Seen a comic book around here?", [], []),
    "nj_comic2": DialogueNode("nj_comic2", "Fine! Fine! I've got the stupid monkey's comic. But only because he took my favourite wall scroll! It contains ancient wisdom passed down the generations!", nj_portrait, [], ["nj_comic3"], "...sure.", [], []),
    "nj_comic3": DialogueNode("nj_comic3", "Not until he gives my wall scroll back. Uh-uh. No way. I don't even speak to him any more.", nj_portrait, [], ["nj_hub"], "Can I have it then?", ["unlock_mk_accusation"], ["mk_quest"]),
    "nj_swap": DialogueNode("nj_swap", "You got it! Sweet! I mean... well done, young one. The road to wisdom and stabbing opens wide before you.", nj_portrait, ["wall_scroll"], ["nj_swap2"], "Your scroll, senpai.", [], []),
    "nj_swap2": DialogueNode("nj_swap2", "Right, yeah. Here you go. Stupid thing's got the spine on the wrong side anyway. Dora's cute though. She's great at stabbing.", nj_portrait, [], ["nj_hub"], "Wisdom, stabbing, got it. And the comic?", ["comic_book"], ["wall_scroll"]),
    "open_crate": DialogueNode("open_crate", "[It looks like the crate's got a luggage lock on it. Something thin and flat should be enough to prise it open.]", crate_portrait, [], ["use_card", None], "", [], []),
    "use_card": DialogueNode("use_card", "[Bingo! You've got a body pillow, fluffy and perfect for plugging a hole. Don't think too hard about the physics of it, we didn't.]", crate_portrait, ["small_label"], [None], "[Use the card to pry open the crate.]", ["body_pillow"], []),
    "enter_storage": LevelSelectNode([], "", [], [], "storage", 0, 0),
    "exit_storage": LevelSelectNode([], "", [], [], "lobby", 0, 3),
    "enter_jungle": LevelSelectNode([], "", [], [], "jungle", 0, 0),
    "exit_jungle": LevelSelectNode([], "", [], [], "lobby", 3, 2),
    "enter_spaceport": LevelSelectNode([], "", [], [], "spaceport", 0, 0),
    "exit_spaceport": LevelSelectNode([], "", [], [], "lobby", 1, 3),
    "enter_dojo": LevelSelectNode([], "", [], [], "dojo", 0, 0),
    "exit_dojo": LevelSelectNode([], "", [], [], "lobby", 4, 1),
    "exit": ExitNode()
}
