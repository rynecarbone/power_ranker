# Publishing Power Rankings to a Website
After generating the html and css files containing your power rankings, you need
a place to host the content. Below is an example of how to create a personal 
GitHub Pages site where you can host your rankings.

# Make a Personal GitHub Pages site
Please refer to GitHub Pages documentation for further details: https://pages.github.com

### Create a repository
- On your GitHub, create a repository called 'username.github.io'
where 'username' is your actual username on GitHub

### Clone the repository 
- If using terminal, cd to folder where you wish to put the project
```bash
git clone https://github.com/username/username.github.io
```

- If using a desktop client, click 'Set up in Desktop' button instead

### Create an index.html
Add an index.html file (default page loaded on your site)

- If using terminal:
```bash
cd username.github.io
echo "Hello World" > index.html
```

- If using a desktop client, add a file called index.html 
to your project with the following content:
```bash
<!DOCTYPE html>
<html>
<body>
<h1>Hello World</h1>
<p>I'm hosted with GitHub Pages.</p>
</body>
</html>
```

### Commit your changes

- If using terminal:
```bash
git add --all
git commit -m "Initial commit"
git push -u origin master
```

- If using a desktop client, enter the repository, commit your changes, and click sync.


### Visit your site
- Navigate to https://username.github.io on any browser

