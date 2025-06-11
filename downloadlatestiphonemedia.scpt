-- Launch Image Capture
tell application "Image Capture" to activate
delay 2

do shell script "echo 'Activated Image Capture'"

tell application "System Events"
	tell process "Image Capture"
		
		-- Wait for window to be ready
		repeat until (exists window 1)
			delay 1
		end repeat
		do shell script "echo 'Main window detected'"

		-- Select iPhone from device list
		if exists row 2 of outline 1 of scroll area 1 of group 1 of splitter group 1 of window 1 then
			select row 2 of outline 1 of scroll area 1 of group 1 of splitter group 1 of window 1
			do shell script "echo 'iPhone selected in device list'"
			delay 2
		else
			do shell script "echo 'iPhone not found in device list'"
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
			do shell script "echo 'Number of items: " & numitems & "'"
		else
			do shell script "echo 'Unable to read number of items — possibly locked'"
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
			do shell script "echo 'Latest file date: " & groupdate & "'"

			select row 1 of table 1 of scroll area 1 of group 2 of splitter group 1 of window 1 
			click button "Download" of group 2 of splitter group 1 of window 1
			do shell script "echo 'Downloaded row 1'"
			delay 2
		else
			do shell script "echo 'Latest item date not found'"
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
					do shell script "echo 'Downloaded row " & i & "'"
					delay 1
				else
					do shell script "echo 'Reached different date at row " & i & "'"
					exit repeat
				end if
			on error errMsg
				do shell script "echo 'Error on row " & i & ": " & errMsg & "'"
				exit repeat
			end try
		end repeat

		delay 3 -- Let downloads finish
		do shell script "echo 'Download loop complete'"
	end tell

	-- Optional: Quit Image Capture at the end
	try
		quit application "Image Capture"
		do shell script "echo 'Quit Image Capture'"
	end try
end tell

-- Final marker for Python
do shell script "echo 'DONE'"
