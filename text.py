#text.py
#Provides functions and classes for organizing text into fields in a console.
#Two useful functions are:
#
# frame(...)
# table(...)
#
#Also the text.Panel() class is useful for creating elaborate text interfaces.
#Rob O.
#Last Updated: 3/14/2014

import re, operator

class FilterError(Exception):
    """Raised when an illegal filter is encountered."""
    
def tformat(string):
    """Takes a string and replaces {{}} filters with variable values.
Filter syntax is {{variable_name.attribute[index]}}.
N.B.: variable_name must be in the global namespace!

EXAMPLES:

>>> x = "foo"
>>> print(tformat("hello {{x}}"))
hello foo
>>> x = 99
>>> print(tformat("hello {{x}}"))
hello 99
>>> class T():
...     pass
...
>>> x = T()
>>> x.y = ["foo", "bar"]
>>> print(tformat("hello {{x.y[0]}}"))
hello foo"""
    
    #Matches character inside double squirlies (e.g., {{anything}})
    filters = re.findall(r"\{\{([^}]+)\}\}", string)
    #valid variable starting characters are underscores and alphabet chars only
    validStartingCharacter = re.compile(r"_|[a-zA-Z]")
    
    filterHead = re.compile(r"^[^\.\[]+")
    indexOrAttribute = re.compile(r"(?:\.(\w+))|(?:(?:\[(?P<item>:_|\w|'|\")+\]))")
    processedFilters = []

    for fil in filters:
        if not validStartingCharacter.match(fil[0]):
            raise FilterError("Variables cannot begin with a number.")
        
        head = filterHead.search(fil).group(0)
        buildUp = globals()[head]
                
        for attribute, item in indexOrAttribute.findall(fil):
            if item:
                try:
                    buildUp = operator.itemgetter(str(item))(buildUp)
                except TypeError:
                    buildUp = operator.itemgetter(int(item))(buildUp)
            elif attribute:
                buildUp = operator.attrgetter(attribute) (buildUp)
            else:
                raise FilterError("Mis-handled by regular expression.")

        processedFilters.append(buildUp)

    replacementString = re.sub(r"\{\{([^}]*)\}\}", "{}", string)
    return replacementString.format(*processedFilters)
            
    
class PanelError(Exception):
    """Raised when an illegal panel operation is attempted."""

class Panel(object):
    """Represents a panel of text that can be subsequently subdivided
into smaller fields."""

    def __init__(self, name,
                 content = "",
                 width = 80,
                 height = 40,
                 padding = 0,
                 topFrame = True,
                 botFrame = True,
                 leftFrame = True,
                 rightFrame = True,
                 parent = None):
        
        self.name = name
        self.content = content
        self.width = width
        self.percent = -1
        self.height = height
        self.padding = padding
        self.topFrame = topFrame
        self.botFrame = botFrame
        self.leftFrame = leftFrame
        self.rightFrame = rightFrame
        self.daughters = []
        self.horizontal = False
        self.vertical = False
        self.parent = parent
        self.index = 0
        self.origin = self.find_origin()
        
    def __getitem__(self, key):
        if self.name == key:
            return self
        else:
            if self.daughters:
                for elem in self.daughters:
                    try:
                        return elem[key]
                    except ValueError:
                        pass

        raise ValueError("No panel named '{}' was found.".format(key))

    def __setitem__(self, key, value):
        if isinstance(value, int):
            self[key].set_percent(value)
        elif isinstance(value, str):
            if self[key].horizontal or self[key].vertical:
                raise PanelError("Subdivided panels cannot hold content.")
            else:
                self[key].content = value
        else:
            raise PanelError("Can only assign strings and integers.")
        

    def __repr__(self):
        return 'Panel("{}")'.format(self.name)

    def set_name(self, name):
        self.name = name

    def set_percent(self, percent):
        """Tells a panel what % of their parent's width/height to use."""

        self.percent = percent
        self.parent.seal()
        
    def set_padding(self, padding):
        """Tells a panel how much padding to use."""
        self.padding = padding
        if self.daughters:
            self.seal()
        else:
            self.parent.seal()

    def set_frames(self, topFrame = False,
                     botFrame = False,
                     leftFrame = False,
                     rightFrame = False):
        """Tells a panel which frames to render."""

        self.topFrame = topFrame
        self.botFrame = botFrame
        self.leftFrame = leftFrame
        self.rightFrame = rightFrame

        self.origin.seal()

    def find_origin(self):
        """Returns the top-level parent of a panel hierarchy."""
        if self.parent:
            return self.parent.find_origin()
        else:
            return self

    
    def subdivide(self,
                subdivisions = 2,
                names = [],
                horizontal = True,
                width = -1,
                height = -1,
                padding = 0,
                topFrame = True,
                botFrame = True,
                leftFrame = True,
                rightFrame = True):
        """Break a panel into 1 or more daughter panels.
Daughter panels will be contained within the scope of their parent."""

        if self.content:
            raise PanelError("Panels with content cannot be subdivided.")
        
        if names and len(names) != subdivisions:
            raise PanelError("The number of names should be equal to the number of subdivisions")
        
        usedWidth = 0
        usedHeight = 0

        if horizontal:
            self.horizontal = True
            self.vertical = False
        else:
            self.horizontal = False
            self.vertical = True

        self.daughters = []   

        availableWidth = self.width - 1*self.leftFrame -1*self.rightFrame - 4*self.padding
        availableHeight = self.height - 1*self.topFrame -1*self.botFrame - 2*self.padding
        
        for count in range(1, subdivisions + 1):
            if self.horizontal:
                self.daughters.append(Panel("{}'s #{} daughter".format(self.name, str(len(self.daughters)+1)),
                                            content = "",
                                            width = availableWidth/subdivisions if width < 0 else width,
                                            height = self.height-1*self.topFrame-1*self.botFrame-2*self.padding if height < 0 else height,
                                            padding = self.padding,
                                            topFrame = self.topFrame,
                                            botFrame = self.botFrame,
                                            leftFrame = self.leftFrame,
                                            rightFrame = self.rightFrame,
                                            parent = self))
            else:
                self.daughters.append(Panel("{}'s #{} daughter".format(self.name, str(len(self.daughters)+1)),
                                            content = "",
                                            width = self.width -1*self.leftFrame -1*self.rightFrame -4*self.padding if width < 0 else width,
                                            height = availableHeight/subdivisions if height < 0 else height,
                                            padding = self.padding,
                                            topFrame = self.topFrame,
                                            botFrame = self.botFrame,
                                            leftFrame = self.leftFrame,
                                            rightFrame = self.rightFrame,
                                            parent = self))
        self.origin.seal()
        if names:
            for count in range(len(names)):
                self.daughters[count].name = names[count]
        
            

    def render_panel(self):
        """Prepare a panel (and all its daughters) for printing."""
        
        if self.horizontal:
            return frame(parallelize([elem.render_panel() for elem in self.daughters]),
                         self.width,
                         self.height,
                         self.padding,
                         self.topFrame,
                         self.botFrame,
                         self.leftFrame,
                         self.rightFrame)
        
        elif self.vertical:
            return frame(columnize([elem.render_panel() for elem in self.daughters], frames = False),
                         self.width,
                         self.height,
                         self.padding,
                         self.topFrame,
                         self.botFrame,
                         self.leftFrame,
                         self.rightFrame)
        
        else:
            #This block of code implements a basic text filter on the content
            #{{variable_name}} gets replaced with its value in globals()
    
##            variables = re.findall(r"\{\{(\w+)\}\}", self.content)
##            content = re.sub(r"\{\{\w+\}\}", "{}", self.content)
##            variables2 = re.findall(r"\{\{(?:(\w+)\.(\w+))\}\}", content)
##            content = re.sub(r"\{\{(?:(\w+)\.(\w+))\}\}", "@@", content)
##            content = content.format(*[globals()[elem] for elem in variables])
##            content = content.replace("@@","{}")
##            print(variables2)
##            content = content.format(*[getattr(globals()[elem[0]],elem[1]) for elem in variables2])
##

            content = tformat(self.content)
            return frame(content,
                         self.width,
                         self.height,
                         self.padding,
                         self.topFrame,
                         self.botFrame,
                         self.leftFrame,
                         self.rightFrame)

    def toggle_direction(self):
        """Toggle the direction daughters are stacked from up-down to left-right
and vice versa."""
        
        if not self.vertical and not self.horizontal:
            raise PanelError("Panel has no direction to change.")

        elif self.vertical:
            self.vertical = False
            self.horizontal = True
            
            self.origin.seal() 
                
        else:
            self.horizontal = False
            self.vertical = True
            
            self.origin.seal()
            

    def seal(self, complete = True):
        """Expands free daughter panels to fill in the entire parent."""
        
        if not self.daughters:
            raise PanelError("Panel has no daughters with which to seal.")

        #N.B.: parentHeight does not include contributions from frame or padding
        parentHeight = self.height-self.topFrame - self.botFrame-self.padding*2
        daughtersHeight = sum([elem.height for elem in self.daughters])

        #N.B.: parentWidth does not include contributions from frame or padding
        parentWidth = self.width-self.leftFrame - self.rightFrame-self.padding*4
        daughtersWidth = sum([elem.width for elem in self.daughters])

        daughtersPercent = sum([elem.percent for elem in self.daughters if elem.percent >= 0])
        freeDaughters = [elem for elem in self.daughters if elem.percent < 0]
        #If the sum of daughter percents does not add to 100, then normalize
        if daughtersPercent > 100:
            for daughter in self.daughters:
                if daughter.percent > 0:
                    daughter.percent = daughter.percent / daughtersPercent
            #the number of daughters with an unspecified percent of -1

        numFreeDaughters = len(freeDaughters)

        
        
        if self.horizontal:
            
            for elem in self.daughters:
                elem.height = parentHeight
                
                if elem.percent < 0:
                    elem.width = int(round(float(parentWidth * (1 - float(daughtersPercent)/100)) / numFreeDaughters))
                else:
                    elem.width = parentWidth * elem.percent / 100
            if complete and freeDaughters:
                daughtersWidth = sum([elem.width for elem in self.daughters])
                freeDaughters[-1].width += parentWidth - daughtersWidth
        
        elif self.vertical:
            for elem in self.daughters:
                elem.width = parentWidth

                if elem.percent<0:
                    elem.height = int(round(float(parentHeight * (1 - float(daughtersPercent)/100)) / numFreeDaughters))
                else:
                    elem.height = parentHeight * elem.percent / 100

            if complete and freeDaughters:
                daughtersHeight = sum([elem.height for elem in self.daughters])
                print("parentHeight({}) - daughterHeight({}) = {}".format(parentHeight, daughtersHeight, parentHeight-daughtersHeight))
                freeDaughters[-1].height += parentHeight - daughtersHeight
        
        else:
            raise PanelError("Panel has no direction.")
def longest_line(multi_line_string):
    """longest_line("A\nMulti-line\nString")

Returns the longest line of a multi-line string."""

    temp = multi_line_string.split("\n")
    longest = 0
    final_string = ""
    
    for line in temp:
        if len(line) > longest:
            longest = len(line)
            final_string = line

    return final_string

def line_height(multi_line_string):
    """line_height("A\nMulti-line\nString")

Returns the height (number of lines) in a multi-line string."""
    
    return len(multi_line_string.split("\n"))
        
def table(*args):
    """table(["list", "of", 4, "objects"],["list", "of", "strings"],...)

Takes lists of strings and returns a single string formatted as a table.

If there is more than one row/column the following assumptions are made:
- The first column and first row are assumed to be headers
- Cells do not span multiple rows or columns

Example:
"""

    columns = []

    #converts the lists of objets in args to lists of strings
    args = [[str(elem2) for elem2 in elem] for elem in args]
    
    if len(args)==1:

        #Find the "tallest" string in the list
        #tallest is the number of lines in the string
        tallest = 0
        for line in args[0]:
            if line_height(line)>tallest:
                tallest = line_height(line)
        
        buildUp = [frame(args[0][0], height = tallest+2)]

        for elem in args[0][1:]:
            buildUp += [frame(elem+("\n"+" "*len(longest_line(elem)))*tallest,
                              height=tallest+2, leftFrame=False)]
  
        return parallelize(buildUp)
        
    elif len(args)>1:

        #longest is the number of cells in the table's longest row
        longest = 0
        for row in args:
            if longest < len(row):
                longest = len(row)

        #all rows should have the same # of cells
        #shorter rows are padded with empty strings
        for row in args:
            if len(row)<longest:
                for count in range(longest-len(row)):
                    row.append("")

        #tallest is a list, with one int element for each row in the table
        #the value of the int is the number of lines in the cell
        tallest = []
        count = 0

        #construct tallest
        for row in args:
            tallest.append(0)
            for line in row:
                if line_height(line)>tallest[count]:
                    tallest[count]=line_height(line)
            count+=1

        #cols is a list of the tables columns
        #the first item of cols is the first table of the column
        cols = [[args[elem][count] for elem in range(len(args)) ] for count in range(longest)]

        #widest is a list with one int element for each column of the table
        #the value of the int is the width of the widest cell in that col
        widest = []
        count = 0

        #construct widest
        for col in cols:
            widest.append(0)
            for line in col:
                if len(longest_line(line))>widest[count]:
                    widest[count]=len(longest_line(line))

            count +=1

        first_row = [frame(args[0][0], width = widest[0]+2, height = tallest[0]+2)]

        for count in range(1,longest):
            first_row += [frame(args[0][count]+("\n"+" "*(widest[count]))*(tallest[0]),
                              height=tallest[0]+2, leftFrame=False)]
        
        all_rows = []
        all_rows.append(first_row)
        next_row = []

        
        #count is the row # and count2 is the column #
        for count in range(1,len(args)):
            next_row = [frame(args[count][0], width = widest[0]+2, height = tallest[count]+2, topFrame=False)]
            for count2 in range(1, longest):
                next_row += [frame(args[count][count2]+("\n"+" "*(widest[count2]))*tallest[count],
                                   height=tallest[count]+2, width = widest[count2]+1,
                                   leftFrame=False, topFrame =False)]
            all_rows.append(next_row)
            
        return columnize([parallelize(elem) for elem in all_rows],
                        frames = False)
    
    else:
        raise IndexError, "table() requires at least one argument"

def columnize(texts=[], width=-1, height=-1, padding=0, frames=True):
    """columnize(["string1","string2",...],width=-1,padding=0)

Frames all text into a standard column width and padding

Example:

>>> print columnize(["Example 1", "Example 2"])
+---------+
|Example 1|
+---------+
|Example 2|
+---------+
"""
    #If no strings were passed, return a blank line of default width
    if len(texts)<1:
        return " "*width

    if height > 0:
        height = height-(len(texts)+1)*frames
        height = height/len(texts)
        height = height + 2*frames
    
    if width < 0:
        biggest = 0
        for elem in texts:
            if len(longest_line(elem)) > biggest:
                biggest = len(longest_line(elem))
        width = biggest+2+4*padding
    column= frame(texts[0],width,height,padding,frames,frames,frames,frames)
    
    for num in range(1,len(texts)):
        column = column + "\n" + frame(texts[num],width,height,padding,
                                       False, frames, frames, frames)
    return column

def parallelize(texts=[], width = -1):
    """parallelize([string1, string2, ...])
Arranges each string in tandem.

NB: Each argument reserves enough screen real-estate to
    print out its largest line of text without overlapping

Example:

>>> print parallelize('''
<Example 1>
A.
B.''','''
<Example 2>
1.
2.
3.
''')
<Example 1><Example 2>
A.         1.
B.         2.
           3."""
    args = texts
    tallest=[]
    lengths=[]
    copy = []
    pattern = re.compile(r"^.*$",flags=re.M)
    #Matches any line of text

    # Find the tallest string (most lines) -> tallest
    # Find the longest line of each string  -> lengths
    
    for text in args:
        if text.count("\n")>tallest.count("\n"):
            tallest = text
        textSize=0
        for line in pattern.findall(text):
            if len(line)>textSize:
                textSize=len(line)
        lengths.append(textSize)

    # Pad strings with blank lines until they are equally tall
    # Width of blank lines is equal to the string's widest line
    for num in range(len(args)):
        copy.append(args[num]+("\n"+" "*(lengths[num]))*(tallest.count("\n")-args[num].count("\n")))
    
    copy = [elem.split("\n") for elem in copy]

    # copy[n][m] is an n-by-m matrix
    # n chooses a string
    # m chooses a line-number

    # Print the 1st line of every string in tandem
    # Then print the 2nd line of every string in tandem
    # Etc..

    screen = ""
    
    for num in range(len(copy[0])):
        output = ""
        for num2 in range(len(copy)):
            output+=copy[num2][num]+" "*(lengths[num2]-len(copy[num2][num]))

        #width < 0 means do not artificially restrict the line width
        if width < 0:
            screen += output+"\n"
        else:
            screen += output[:width]+"\n"

    #Remove the last newline
    screen=screen[:-1]
    
    return screen

def clean(text):
    """Removes unnecessary white-space for easier formatting down-stream."""

    #remove leading new-lines
    text = re.sub(r"^\n+","",text)
    
    #replace tabs with 4 spaces
    text = re.sub(r"\t","    ",text)

    #remove singular new-lines
    #UNLESS the next line starts with whitespace
    text = re.sub(r"([^\n ]) *\n(\S)",r"\1 \2",text)
    
    #remove leading white-space from every line
    text = re.sub(r"^ +","",text,flags=re.M)
        
    #fix broken hyphenation
    text = re.sub(r"(\w-{2,}) ",r"\1",text)
    
    #remove trailing white-space from each line
    text = re.sub(r"(\S) *\n",r"\1\n",text)
    
    return text


def bookify(text,width=80,padding=0):
    """Formats text such that it would appear in a book:

Cleans text.
Removes double-space after periods.
Inserts page-breaks at entity reference '&pb;'
Inserts four spaces at the beginnning of paragraphs (if necessary)"""

    text = clean(text)

    #Remove double-space after periods.
    text = re.sub(r"\.  ",". ",text)
    
    #insert page-break at entity reference &pb; (formatting)
    text = re.sub(r"(\s?\&pb;\s?)","\n"+"-"*(width-4*padding)+"\n",text)

    #if characters > width - 4 spaces - padding
    #add four spaces to the beginning of the paragraph (formatting)
    pattern = r"^([^\n]{"+str(width+1+padding*2)+r"})"
    text = re.sub(pattern,r"    \1",text,flags=re.M)

    return text

def constrain(text, width=-1):
    """trim lines to a maximum of width characters"""
    
    longest = 0

    
    #Matches any word
    pattern = re.compile(r"\b\S+\b")
    
    for elem in pattern.findall(text):
        if len(elem) > longest:
            longest = len(elem)

    #Matches any line of text that has at least two pipes    
    temp = r"^.*\|.*\|.*$"

    #Nested RE:
    #For every line with pipes pipes:
    #   For every space:
    #       Replace it with a temporary character
    #
    #(This prevents whitespace inside a frame from breaking
    text = re.sub(temp, lambda m: re.sub(r" ", "`",m.group(0)), text, flags=re.M)

    
    #Matches the maximum number of characters terminated by a space
    #that will fit in width
    pattern = r"(.{,"+str(width)+r"})(\s|(\w--?\w)|$)"

    text = re.sub(pattern,
            lambda m: m.group(0) if re.match(r"^\+-*\+^", m.group(0)) else (m.group(1)+"\n" if len(m.group(2))<2 else m.group(1)+m.group(2)[:-1]+"\n"+m.group(2)[-1:]),
                  text)

    
    
    #Revert temporary characters to spaces
    text = re.sub("`", " ", text)

    if text[-1]=='\n':
        text = text[:-1]

    return text
    

def frame(text, width=-1, height=-1, padding=0,
          topFrame=True, botFrame=True,
          leftFrame=True, rightFrame=True):
    
    """Constrains text to fit within a specified width, then adds frame to text.

NB: padding < 0 turns all frames off
NB: width < 0 sets width to the length of the longest line


EXAMPLES:
       
>>> print frame("Example Text")
+------------+
|Example Text|
+------------+

>>> print frame(frame("Example Text"))
+--------------+
|+------------+|
||Example Text||
|+------------+|
+--------------+

>>> print frame("Extra Padding",20,1)
+------------------+
|                  |
|  Extra Padding   |
|                  |
+------------------+

print frame('''Text that overflows the width
parameter is placed on the next line.''',20)
+------------------+
|Text that         |
|overflows the     |
|width             |
|parameter is      |
|placed on the next|
|line.             |
+------------------+

>>> print frame('''If a word (e.g., antidisestablishmentarianism)
exceeds the width, the offending word is truncated.''',20)
+------------------+
|If a word (e.g.,  |
|antidisestablishme|
|exceeds the width,|
|the offending word|
|is truncated.     |
+------------------+

>>> print frame('''The ASCII frames can be easily
removed by setting the padding parameter to -1.''', 20, padding=-1)

The ASCII frames can
be easily
removed by setting
the padding
parameter to -1."""

    if padding<0:
        padding=0
        topFrame = False
        botFrame = False
        leftFrame = False
        rightFrame = False
        
    fNum = 0 + (1 if leftFrame else 0) + (1 if rightFrame else 0)
    
   #if string is empty, then add at least one space
    if len(text)<1:
        text= " "+" "*(width-fNum-padding*4)

    if width<0:
        widest = 0
        pattern = re.compile(r"^.*$",flags=re.M)
        #Matches any line of text
        for elem in pattern.findall(text):
            if len(elem)>widest:
                widest = len(elem)
        width=widest+4*padding+fNum
##        if width>80:
##            width = 80
                
    #trim lines to a maximum of width - 4*padding - frame characters
    text = constrain(text, width-4*padding-fNum)
    
    #Add Left Padding
    text = re.sub(r"^","  "*padding,text,flags=re.M)
    
    #Add Top and Bottom Padding
    text="\n"*padding+text+"\n"*padding

    
    
    #Add Side Frames
    if leftFrame or rightFrame:
        #Yank as many chars as will fit in width (-1 for left frame and -2 per
        #                                         degree of left-padding)
        #Pad the yanked text from the right with spaces
        
        text = re.sub(r"(^.{,"+str(width-2*padding-fNum)+"})",
                      r"\1"+" "*width,
                      text, flags=re.M)
        #Grab the first width-fNum chars and frame them
        if width-fNum>0:
            
            text = re.sub(r"(^.{"+str(width-fNum)+"}).*",
                          ("|" if leftFrame else "")+r"\1"+("|"if rightFrame else ""),
                          text,flags=re.M)
        if width-fNum==0:
            text= re.sub(r"(^.*)","||",text,flags=re.M)
        if width-fNum==-1:
            text= re.sub(r"(^.*)","|",text,flags=re.M)
        if width-fNum < -1:
            text = re.sub(r"(^.*$)","",text,flags=re.M)
        
    
    
    
    #Add Top and Bottom Frame
    if topFrame:
        if width-fNum>0:
            text=("+" if leftFrame else "-")+"-"*(width-2)+("+" if rightFrame else "-")+"\n"+text
        if width-fNum==0:
            text=("+" if leftFrame else "-")+("+\n" if rightFrame else "-\n")+text
        if width-fNum==-1:
            text=("+\n" if (leftFrame or rightFrame) else "-\n")+text

    if height > -1:
            text+=(("\n|" if leftFrame else "\n")+" "*(width-fNum)+("|" if rightFrame else ""))*height
            temp = text.split("\n",height+(1 if topFrame else 0))
            text = "\n".join(temp[:-1-padding-botFrame-topFrame])
            text+=("\n|"+" "*(width-fNum)+"|")*padding
            
    if botFrame:
        
        
            
        if width-fNum>0:
            text = text+"\n"+("+" if leftFrame else "-")+"-"*(width-2)+("+" if rightFrame else "-")
        if width-fNum==0:
            text=text+("\n+" if leftFrame else "\n-")+("+" if rightFrame else "-")
        if width-fNum==-1:
            text=text+("\n+" if (leftFrame or rightFrame) else "\n-")
            
    return text


##if __name__ == "__main__":
##    import doctest
##    doctest.testmod()
