on run {input, parameters}
	set theText to input as string
	set userChoice to choose from list {"Translate this sentence", "Summary this content", "Explain Code", "Polish", "Improve Report"} with prompt "Choose an action:"
	
	if userChoice is false then
		return input
	else
		set action to item 1 of userChoice
	end if
	
	set actionCommand to ""
	
	if action is "Translate this sentence" then
		set actionCommand to "translate"
	else if action is "Summary this content" then
		set actionCommand to "summary"
	else if action is "Explain Code" then
		set actionCommand to "explainCode"
	else if action is "Polish" then
		set actionCommand to "polish"
	else if action is "Do My Job" then
		set actionCommand to "anotherCoolAction"
	end if
	
	-- Call the Python script with the chosen action and text
	do shell script "/opt/homebrew/bin/python3.12 ~/bin/ofelia/ofelia.py " & quoted form of theText & " " & actionCommand
	
	return input
end run