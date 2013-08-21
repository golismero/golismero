description = [[
The httprecon project is doing some research in the field of web server
fingerprinting, also known as http fingerprinting. The goal is the
highly accurate identification of given httpd implementations. This is
very important within professional vulnerability analysis.

The application works very straight forward. After the user has defined
the target service which shall be fingerprinted, a common tcp
connection is opened to the destination port. If the connection could
be established, the http requests are sent to the target service. This
one will shall react with responses. These could be dissected to
identify some specific fingerprint elements. Those elements are looked
up in the local fingerprint database. If there is a match, the
according implementation is flagged as "identified". All these flags
were counted so httprecon is able to determine which implementation has
the best match rate.

The possibility of fingerprinting is not a vulnerability in a
traditional way which allows to compromise a host. It is more a flaw or
exposure which may provide the foundation for further enumeration and
specific attack scenarios.

For more details about http fingerprinting, httprecon and the available
implementations visit the official project web site at:
http://www.computec.ch/projekte/httprecon/
]]

--@output
-- PORT   STATE SERVICE REASON
-- 80/tcp open  http    syn-ack
-- | httprecon:     Implementation     Score  Hits
-- | 1   Microsoft IIS 6.0  77     38
-- | 2   Apache 2.0.46      70     35
-- | 3   Apache 2.0.54      70     34
-- | 4   Apache 2.2.2       70     34
-- | 5   Apache 2.2.8       68     33
-- | 6   AOLserver 3.4.2    68     34
-- | 7   Apache 1.3.33      68     33
-- | 8   Apache 1.3.34      68     33
-- | 9   Apache 2.2.3       68     33
-- |_10  Zeus 4.3           68     33

--@changelog
-- v0.5 | 05/02/2010 | Marc Ruef | Added argument support (disable test requests)
-- v0.4 | 05/01/2010 | Marc Ruef | Finalized fingerprint analysis
-- v0.3 | 04/30/2010 | Marc Ruef | Added error handling and debugging mode
-- v0.2 | 04/08/2010 | Marc Ruef | More test requests and fingerprint dissection
-- v0.1 | 03/23/2010 | Marc Ruef | First alpha running basic get test

--@todos
-- Add further test requests (e.g. DELETE, OPTIONS, Attack Request)
-- Add confidence of determination in percent
-- Add possibility of adding/submitting new/unknown fingerprints
-- Add filter for header order analysis (e.g. no X-header, no cookies)
-- Add additional user argument settings (e.g. resource for get_nonexisting)

author = "Marc Ruef, marc.ruef-at-computec.ch, http://www.computec.ch/mruef/"
license = "Same as Nmap--See http://nmap.org/book/man-legal.html"
categories = {"default", "safe"}

require "shortport"
require "tab"
require "http"
require "stdnse"

result = {}	-- Global result data

portrule = shortport.port_or_service({80, 443}, {"http", "https"}, {"tcp"})

action = function(host, port)
	local response		-- Response from the server

	local maxresults = 10	-- Top listing of matches; change to what you like
	if nmap.registry.args.httprecontoplist then
		maxresults = tonumber(nmap.registry.args.httprecontoplist)
	end

	-- Collect http responses
	if nmap.registry.args.httprecontestgetexisting ~= "0" then
		response = send_http_request(host, port, "GET", "/")
		if type(response) == "table" then
			identify_fingerprint(response, "scripts/httprecon/get_existing/")
		else
			stdnse.print_debug(1, "httprecon: Failed to do get_existing analysis")
		end
	end

	if nmap.registry.args.httprecontestgetnonexisting ~= "0" then
		response = send_http_request(host, port, "GET", "/404test_.html")
		if type(response) == "table" then
			identify_fingerprint(response, "scripts/httprecon/get_nonexisting/")
		else
			stdnse.print_debug(1, "httprecon: Failed to do get_nonexisting analysis")
		end
	end

	if nmap.registry.args.httprecontestgetlong ~= "0" then
		response = send_http_request(host, port, "GET", "/" .. string.rep("a", 1024))
		if type(response) == "table" then
			identify_fingerprint(response, "scripts/httprecon/get_long/")
		else
			stdnse.print_debug(1, "httprecon: Failed to do get_long analysis")
		end
	end

	if nmap.registry.args.httprecontestheadexisting ~= "0" then
		response = send_http_request(host, port, "HEAD", "/")
		if type(response) == "table" then
			identify_fingerprint(response, "scripts/httprecon/head_existing/")
		else
			stdnse.print_debug(1, "httprecon: Failed to do head_existing analysis")
		end
	end

	-- Generate output
	if type(result) == "table" then
		stdnse.print_debug(1, "httprecon: %d matches found", #result)

		if #result > 0 then
			for i = 1, #result, 1 do
				for j = 2, #result do
					if result[j].score > result[j-1].score then
						temp = result[j-1]
						result[j-1] = result[j]
						result[j] = temp
					end
				end
			end

			local t = tab.new(4)
			tab.addrow(t, "Pos", "Implementation", "Score", "Hits")
			for i=1, #result, 1 do
				tab.addrow(t,
					tostring(i),
					result[i].matchname,
					tostring(result[i].score),
					tostring(result[i].count)
				)

				if i == maxresults then
					stdnse.print_debug(1, "httprecon: %d top matches displaying", i)
					break
				end
			end
			return tab.dump(t)
		end
	else
		stdnse.print_debug(1, "httprecon: Failed to do whole analysis")
	end
end

function send_http_request(host, port, method, resource)
	local res	-- Response from the web server

	if method == "HEAD" then
		stdnse.print_debug(2, "httprecon: Sending head request")
		res = http.head(host, port, resource)
	else
		stdnse.print_debug(2, "httprecon: Sending get request")
		res = http.get(host, port, resource)
	end

	if type(res) == "table" then
		stdnse.print_debug(2, "httprecon: Received response")

--		for i=1, #res.rawheader, 1 do
--			stdnse.print_debug(3, "httprecon: \t%s", res.rawheader[i])
--		end

		return res
	else
		stdnse.print_debug(1, "httprecon: Failed to receive response for %s", method .. " " .. resource)
		return ""
	end
end

function identify_fingerprint(response, database)
	stdnse.print_debug(2, "httprecon: Identifying fingerprint in %s", database)

	find_match_in_db(database .. "accept-range.fdb",		get_header_value(get_header_line(response.rawheader, "Accept-Ranges", false)), 1)
	find_match_in_db(database .. "banner.fdb",				get_header_value(get_header_line(response.rawheader, "Server", false)), 3)
	find_match_in_db(database .. "cache-control.fdb",		get_header_value(get_header_line(response.rawheader, "Cache-Control", false)), 2)
	find_match_in_db(database .. "connection.fdb",			get_header_value(get_header_line(response.rawheader, "Connection", false)), 2)
	find_match_in_db(database .. "content-type.fdb",		get_header_value(get_header_line(response.rawheader, "Content-Type", false)), 1)
	find_match_in_db(database .. "etag-legth.fdb",			string.format("%s", string.len(get_header_value(get_header_line(response.rawheader, "ETag", false)))), 3)
	find_match_in_db(database .. "etag-quotes.fdb",			get_quotes(get_header_value(get_header_line(response.rawheader, "ETag", false))), 2)
	find_match_in_db(database .. "header-capitalafterdash.fdb",	string.format("%s", capital_after_dash(analyze_header_order(response.rawheader))), 2)
	find_match_in_db(database .. "header-order.fdb",		analyze_header_order(response.rawheader), 5)
	find_match_in_db(database .. "header-space.fdb",		string.format("%s", header_space(response.rawheader)), 2)
	find_match_in_db(database .. "htaccess-realm.fdb",		get_realm(get_header_line(response.rawheader, "WWW-Authenticate", false)), 3)
	find_match_in_db(database .. "pragma.fdb",				get_header_value(get_header_line(response.rawheader, "Pragma", false)), 2)
	find_match_in_db(database .. "protocol-name.fdb",		get_protocol_name(response['status-line']), 1)
	find_match_in_db(database .. "protocol-version.fdb",	get_protocol_version(response['status-line']), 2)
	find_match_in_db(database .. "statuscode.fdb",			get_status_code(response.status), 4)
	find_match_in_db(database .. "statustext.fdb",			get_status_text(response['status-line']), 4)
	find_match_in_db(database .. "vary-capitalize.fdb",		string.	("%s", has_capital(get_header_line(response.rawheader, "Vary", false))), 2)
	find_match_in_db(database .. "vary-delimiter.fdb",		vary_delimiter(get_header_line(response.rawheader, "Vary", false)), 2)
	find_match_in_db(database .. "vary-order.fdb",			get_header_value(get_header_line(response.rawheader, "Vary", false)), 3)
	find_match_in_db(database .. "x-powered-by.fdb",		get_header_value(get_header_line(response.rawheader, "X-Powered-By", false)), 3)
end

function find_match_in_db(databasefile, fingerprint, basescore)
	local database		= read_from_file(databasefile)	-- Content of fingerprint database
	local delimiterpos					-- Position of delimiter
	local name						-- Name of implementation
	local pattern						-- Pattern of fingerprint
	local arraypos						-- Position in array

	stdnse.print_debug(3, "httprecon: Looking for matches of %s", fingerprint)
	for i=1, #database, 1 do
		delimiterpos = string.find(database[i], ";")

		if type(delimiterpos) == "number" then
			name = string.sub(database[i], 1, delimiterpos - 1)
			pattern = string.sub(database[i], delimiterpos + 1)

			if type(pattern) == "string" and pattern ~= "" and type(name) == "string" and name ~= "" then
				if fingerprint == pattern then
					arraypos = in_array(result, name)

					stdnse.print_debug(4, "httprecon: Find match for %s", name)
					if type(arraypos) == "number" then
						result[arraypos] = {
							matchname = name,
							count = result[arraypos].count + 1,
							score = result[arraypos].score + basescore
							}
					else
						result[#result + 1] = {
							matchname = name,
							count = 1,
							score = basescore
							}
					end
				end
			end
		end
	end

	return true
end

--
-- HTTP Data Dissection
--

function get_protocol_name(statusline)
	if type(statusline) == "string" then
		if string.len(statusline) > 4 then
			return trim(string.sub(statusline, 1, 4))
		end
	end
end

function get_protocol_version(statusline)
	if type(statusline) == "string" then
		if string.len(statusline) > 8 then
			return trim(string.sub(statusline, 6, 8))
		end
	end
end

function get_status_text(statusline)
	if type(statusline) == "string" then
		if string.len(statusline) > 14 then
			return trim(string.sub(statusline, 14))
		end
	end
end

function get_status_code(status)
	if type(status) == "number" then
		return string.format("%s", status)
	end
end

function get_header_line(rawheader, line, casesensitive)
	local headerline	-- Line of header

	if type(rawheader) == "table" then
		for i=1, #rawheader, 1 do
			headerline = string.sub(rawheader[i], 1, string.len(line) + 2)

			if headerline ~= nil and headerline ~= "" then
				if casesensitive == true and string.find(headerline, line .. ": ", 1, true) ~= nil then
					stdnse.print_debug(3, "httprecon: Get header line %s (with case-sensitive)", rawheader[i])
					return rawheader[i]
				elseif casesensitive == false and string.find(string.lower(headerline), string.lower(line) .. ": ", 1, true) ~= nil then
					stdnse.print_debug(3, "httprecon: Get header line %s", rawheader[i])
					return rawheader[i]
				end
			end
		end
	end

	return ""
end

function get_header_value(headerline)
	local headervalue = ""					-- Value of headerline
	local delimiterpos = string.find(headerline, ":")	-- Delimiter position of header

	if type(delimiterpos) == "number" then
		headervalue = trim(string.sub(headerline, delimiterpos+1))
	end

	if type(headervalue) == "string" then
		stdnse.print_debug(4, "httprecon: Extracted header value %s", headervalue)
		return headervalue
	end
end

function get_realm(headerline)
	if type(headerline) == "string" then
		return string.match(headerline, 'realm="(.-)"')
	end
end

--
-- Fingerprint Collection
--

function analyze_header_order(rawheader)
	local headerorder = ""	-- String of header values
	local delimiterpos = 0	-- Delimiter position
	local headername = ""	-- Name of header line

	if type(rawheader) == "table" then
		for i=1, #rawheader, 1 do
			delimiterpos = string.find(rawheader[i], ":")

			if type(delimiterpos) == "number" and delimiterpos > 0 then
				headername = string.sub(rawheader[i], 1, delimiterpos-1)

				if type(headername) == "string" then
					headerorder = headerorder .. headername

					if rawheader[i+1] ~= nil and rawheader[i+1] ~= "" then
						headerorder = headerorder .. ","
					end
				end
			end
		end
	end
	stdnse.print_debug(3, "httprecon: Get header order %s", headerorder)

	return headerorder
end

function get_quotes(headerline)
	local doublequotes = ""
	local singlequotes = ""

	doublequotes = string.find(headerline, '"')
	singlequotes = string.find(singlequotes, "'")

	if doublequotes == "number" and doublequotes ~= "" then
		return '"'
	elseif singlequotes == "number" and singlequotes ~= "" then
		return "'"
	else
		return ""
	end
end

function has_capital(str)
	if str ~= nil then
		if string.lower(str) == str then
			return 0
		else
			return 1
		end
	else
		return ""
	end
end

function capital_after_dash(str)
	local dashpos = string.find(str, "-", 1, true)

	if dashpos ~= nil then
		local afterdash = string.sub(str, dashpos+1, dashpos+1)

		if afterdash ~= nil and string.upper(afterdash) == afterdash then
			return 1
		elseif afterdash ~= nil and string.lower(afterdash) == afterdash then
			return 0
		end
	else
		return ""
	end
end

function header_space(rawheader)
	if rawheader ~= nil then
		for i=1, #rawheader, 1 do
			if string.find(rawheader[i], ": ", 1, true) then
				return 1
			end
		end
	end

	return 0
end

function vary_delimiter(str)
	if string.find(str, ", ") then
		return ", "
	elseif string.find(str, ",") then
		return ","
	else
		return ""
	end
end

--
-- Basic Functions
--

function trim(string)
      return string.gsub(string, "^%s*(.-)%s*$", "%1")
end

function in_array(array, find)
	for i=1, #array, 1 do
		if array[i].matchname == find then
			return i
		end
	end
end

function read_from_file(file)
	local filepath = nmap.fetchfile(file)

	if not filepath then
		stdnse.print_debug(1, "httprecon: File %s not found", file)
		return ""
	end

	local f, err, _ = io.open(filepath, "r")
	if not f then
		stdnse.print_debug(1, "httprecon: Failed to open file %s", file)
		return ""
	end

	local line, ret = nil, {}
	while true do
		line = f:read()
		if not line then break end
		ret[#ret+1] = line
	end

	f:close()

	return ret
end
