% include('global/header.tpl', title='Turning whois... to JSON')
<div class="container">
    <div class="starter-template">
        <h1>Welcome to whoisjs.com</h1>
        <p class="lead">
            Need WHOIS? Need it in an application accessible method? <br />
            If you need this, then dnsjson.com is for you!
        </p>
        <p>&nbsp;</p>
        <div class="panel panel-primary">
            <div class="panel-heading">
                <h2 class="panel-title">Lookup a domain</h3>
            </div>
            <div class="panel-body">
                <form class="form-inline" method="POST" action="/">
                    <fieldset>
                        <div class="form-group">
                            <input type="text" name="domain" class="form-control" id="domain"
                                placeholder="example.com">
                        </div>
                        <div class="form-group">
                            <button type="submit" class="btn btn-primary">Lookup</button>
                        </div>
                    </fieldset>
                </form>
            </div>
        </div>
    </div>
</div>
% include('global/footer.tpl')