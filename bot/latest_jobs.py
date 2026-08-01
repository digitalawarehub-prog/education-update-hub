def generate_latest_jobs(jobs):

    rows = []

    for i, job in enumerate(jobs, start=1):

        rows.append(f"""
<tr>
<td>{i}</td>

<td>
<a href="{job.get('html_file', '#')}">
{job.get('title','')}
</a>
</td>

<td>{job.get('start_date','-')}</td>

<td>{job.get('last_date','-')}</td>

<td>
<a class="apply-btn"
href="{job.get('apply_link', job.get('url','#'))}"
target="_blank">
Apply Online
</a>
</td>

</tr>
""")

    return f"""
<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<title>Latest Government Jobs</title>

<style>

body{font-family:Arial;background:#f5f5f5;margin:0}

.container{
width:95%;
margin:auto;
padding:20px;
}

table{
width:100%;
border-collapse:collapse;
background:#fff;
}

th{
background:#082567;
color:#fff;
padding:14px;
}

td{
padding:12px;
border-bottom:1px solid #ddd;
}

tr:hover{
background:#f9f9f9;
}

a{
text-decoration:none;
color:#003399;
font-weight:bold;
}

.apply-btn{
background:#14833b;
color:#fff;
padding:8px 16px;
border-radius:4px;
display:inline-block;
}

.apply-btn:hover{
background:#0f6d30;
}

</style>

</head>

<body>

<div class="container">

<h2>Latest Government Jobs 2026</h2>

<table>

<tr>

<th>S.No.</th>

<th>Job Title</th>

<th>Online Start</th>

<th>Last Date</th>

<th>Apply Online</th>

</tr>

{''.join(rows)}

</table>

</div>

</body>

</html>
"""
