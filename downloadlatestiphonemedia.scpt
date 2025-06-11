-- Launch Image Capture
tell application "Image Capture" to activate
delay 2

tell application "System Events"
	tell process "Image Capture"
		-- Wait until the main window is ready
		repeat until (exists window 1)
			delay 2
		end repeat
		
		-- Select first iPhone
		if exists row 2 of outline 1 of scroll area 1 of group 1 of splitter group 1 of window 1 then
			select row 2 of outline 1 of scroll area 1 of group 1 of splitter group 1 of window 1
		end if
		
		-- Get number of items on iphone
		set numitems to 0
		if exists value of static text 2 of window 1 then
			set numitemsstring to value of static text 2 of window 1	
			set splitParts to words of numitemsstring
			set itemCountText to item 1 of splitParts
			set numitems to itemCountText as integer
			--do shell script "echo " & quoted form of numitems
			--display dialog "Item count is: " & numitems
		else
			display dialog "Please unlock your iPhone."	
		end if
				
		-- Find date of latest file and download latest file
		set groupdate to ""
		if exists value of static text 1 of UI element 4 of row 1 of table 1 of scroll area 1 of group 2 of splitter group 1 of window 1 then
		            set groupdate to value of static text 1 of UI element 4 of row 1 of table 1 of scroll area 1 of group 2 of splitter group 1 of window 1
					set oldDelimiters to AppleScript's text item delimiters
					set AppleScript's text item delimiters to " at"
					set groupdate to text item 1 of groupdate
					--display dialog "Date: " & groupdate
					
					-- Download 
					select row 1 of table 1 of scroll area 1 of group 2 of splitter group 1 of window 1 
					click button "Download" of group 2 of splitter group 1 of window 1					
			else
			display dialog "Value not found"
		end if
		
		repeat with i from 2 to numitems
            set datevar to value of static text 1 of UI element 4 of row i of table 1 of scroll area 1 of group 2 of splitter group 1 of window 1
			set oldDelimiters to AppleScript's text item delimiters
			set AppleScript's text item delimiters to " at"
			set datevar to text item 1 of datevar
			--display dialog "Date: " & datevar
			
			if datevar = groupdate then
				select row i of table 1 of scroll area 1 of group 2 of splitter group 1 of window 1 
				click button "Download" of group 2 of splitter group 1 of window 1
			else
				exit repeat
			end if
		end repeat
	end tell
	quit application "Image Capture"
end tell
