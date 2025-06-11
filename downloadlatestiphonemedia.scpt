-- Launch Image Capture
tell application "Image Capture" to activate
delay 2

--display dialog "Activated Image Capture" buttons {"OK"}

tell application "System Events"
	tell process "Image Capture"
		
		-- Wait for window to be ready
		repeat until (exists window 1)
			delay 1
		end repeat
		--display dialog "Main window detected" buttons {"OK"}

		-- Select iPhone from device list
		if exists row 2 of outline 1 of scroll area 1 of group 1 of splitter group 1 of window 1 then
			select row 2 of outline 1 of scroll area 1 of group 1 of splitter group 1 of window 1
			--display dialog "iPhone selected in device list" buttons {"OK"}
			delay 2
		else
			display dialog "Please connect and unlock your iPhone." buttons {"OK"}
			error "iPhone device not found"
		end if

		-- Get number of items
		set numitems to 0
		if exists value of static text 2 of window 1 then
			set numitemsstring to value of static text 2 of window 1	
			set splitParts to words of numitemsstring
			set itemCountText to item 1 of splitParts
			set numitems to itemCountText as integer
			--display dialog "Number of items: " & numitems buttons {"OK"}
		else
			display dialog "Please unlock your iPhone." buttons {"OK"}
			error "iPhone is locked or unreadable"
		end if

		-- Check and download the latest item
		set groupdate to ""
		if exists value of static text 1 of UI element 4 of row 1 of table 1 of scroll area 1 of group 2 of splitter group 1 of window 1 then
			set groupdate to value of static text 1 of UI element 4 of row 1 of table 1 of scroll area 1 of group 2 of splitter group 1 of window 1
			set oldDelimiters to AppleScript's text item delimiters
			set AppleScript's text item delimiters to " at"
			set groupdate to text item 1 of groupdate
			set AppleScript's text item delimiters to oldDelimiters
			--display dialog "Latest file date: " & groupdate buttons {"OK"}

			select row 1 of table 1 of scroll area 1 of group 2 of splitter group 1 of window 1 
			click button "Download" of group 2 of splitter group 1 of window 1
			repeat while (name of button 1 of group 2 of splitter group 1 of window 1 is "Cancel")
				delay 0.2
			end repeat
			--display dialog "Downloaded row 1" buttons {"OK"}
		else
			display dialog "Unable to locate latest media file." buttons {"OK"}
			error "No media rows found"
		end if

		-- Loop to download all items from the same date
		repeat with i from 2 to numitems
			try
				set datevar to value of static text 1 of UI element 4 of row i of table 1 of scroll area 1 of group 2 of splitter group 1 of window 1
				set oldDelimiters to AppleScript's text item delimiters
				set AppleScript's text item delimiters to " at"
				set datevar to text item 1 of datevar
				set AppleScript's text item delimiters to oldDelimiters

				if datevar = groupdate then
					select row i of table 1 of scroll area 1 of group 2 of splitter group 1 of window 1 
					click button "Download" of group 2 of splitter group 1 of window 1
					repeat while (name of button 1 of group 2 of splitter group 1 of window 1 is "Cancel")
						delay 0.2
					end repeat
					--display dialog "Downloaded row " & i buttons {"OK"}
				else
					display dialog "Reached different date at row " & i buttons {"OK"}
					exit repeat
				end if
			on error errMsg
				display dialog "Error on row " & i & ": " & errMsg buttons {"OK"}
				exit repeat
			end try
		end repeat

		delay 3 -- Let downloads finish
		--display dialog "Download loop complete" buttons {"OK"}
	end tell

	-- Optional: Quit Image Capture at the end
	try
		quit application "Image Capture"
		--display dialog "Quit Image Capture" buttons {"OK"}
	end try
end tell

-- Final marker (visual only)
display dialog "DONE" buttons {"OK"}
