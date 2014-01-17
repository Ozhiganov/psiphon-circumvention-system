
#import "AddressField.h"
//#include "SGTabDefines.h"

@implementation AddressField
@synthesize state = _state;

- (id)initWithDelegate:(id<UITextFieldDelegate>)delegate {
    if (self = [super initWithFrame:CGRectMake(0, 0, 200., 30.)]) {
        self.delegate = delegate;
        self.autoresizingMask = UIViewAutoresizingFlexibleWidth;
        self.contentVerticalAlignment = UIControlContentVerticalAlignmentCenter;
        self.placeholder = NSLocalizedString(@"Enter URL or search query here", nil);
        self.keyboardType = UIKeyboardTypeASCIICapable;
        self.autocapitalizationType = UITextAutocapitalizationTypeNone;
        self.autocorrectionType = UITextAutocorrectionTypeNo;
        self.borderStyle = UITextBorderStyleRoundedRect;
        self.clearButtonMode = UITextFieldViewModeWhileEditing;
        self.textColor = [UIColor darkTextColor];
        
        self.leftView = [[UIImageView alloc] initWithImage:[UIImage imageNamed:@"magnify"]];
        self.leftViewMode = UI_USER_INTERFACE_IDIOM() == UIUserInterfaceIdiomPhone ?
        UITextFieldViewModeUnlessEditing : UITextFieldViewModeAlways;
        self.rightViewMode = UITextFieldViewModeUnlessEditing;
        
        CGRect btnRect = CGRectMake(0, 0, 22, 22);
        _reloadItem = [UIButton buttonWithType:UIButtonTypeCustom];
        self.reloadItem.frame = btnRect;
        self.reloadItem.backgroundColor = [UIColor clearColor];
        self.reloadItem.showsTouchWhenHighlighted = YES;
        [self.reloadItem setImage:[UIImage imageNamed:@"reload"] forState:UIControlStateNormal];
        
        _stopItem = [UIButton buttonWithType:UIButtonTypeCustom];
        self.stopItem.frame = btnRect;
        self.stopItem.backgroundColor = [UIColor clearColor];
        self.stopItem.showsTouchWhenHighlighted = YES;
        [self.stopItem setImage:[UIImage imageNamed:@"stop"] forState:UIControlStateNormal];
        
        self.state = SearchFieldStateDisabled;
        
        self.inputAccessoryView = [self generateInputAccessoryView];
    }
    return self;
}

- (void)drawTextInRect:(CGRect)rect {
    if (self.editing)
        [super drawTextInRect:rect];
    else {
        NSString *text = [self.text stringByReplacingOccurrencesOfString:@"http://" withString:@""];
        text = [text stringByReplacingOccurrencesOfString:@"https://" withString:@""];
        [text drawInRect:rect withFont:self.font
           lineBreakMode:NSLineBreakByTruncatingTail
               alignment:self.textAlignment];
    }
}

- (UIView *)generateInputAccessoryView {
    UIToolbar *_inputAccessory = [[UIToolbar alloc] initWithFrame:CGRectMake(0, 0, self.superview.bounds.size.width, 44.)];
    _inputAccessory.autoresizingMask = UIViewAutoresizingFlexibleWidth;
    if (UI_USER_INTERFACE_IDIOM() == UIUserInterfaceIdiomPhone) {
        _inputAccessory.translucent = YES;
        _inputAccessory.tintColor = kTabColor;
    }
    
    UIBarButtonItem *btn, *flex, *fix;
    flex = [[UIBarButtonItem alloc] initWithBarButtonSystemItem:UIBarButtonSystemItemFlexibleSpace
                                                         target:nil action:nil];
    fix = [[UIBarButtonItem alloc] initWithBarButtonSystemItem:UIBarButtonSystemItemFixedSpace
                                                        target:nil action:nil];
    fix.width = 10;
    
    NSArray *titles = @[@":", @".", @"-", @"/", @".com"];
    NSMutableArray *buttons = [NSMutableArray arrayWithCapacity:titles.count];
    [buttons addObject:flex];
    for (NSString *title in titles) {
        btn = [[UIBarButtonItem alloc] initWithTitle:title
                                               style:UIBarButtonItemStyleBordered
                                              target:self
                                              action:@selector(addText:)];
        if (UI_USER_INTERFACE_IDIOM() == UIUserInterfaceIdiomPhone)
            btn.tintColor = [UIColor lightGrayColor];
        
        btn.width = 40.;
        [buttons addObject:btn];
        [buttons addObject:fix];
    }
    [buttons addObject:flex];
    _inputAccessory.items = buttons;
    return _inputAccessory;
}

- (IBAction)addText:(UIBarButtonItem *)sender {
    [self insertText:sender.title];
}

- (void)setState:(SearchFieldState)state {
    if (_state == state)
        return;
    
    _state = state;
    switch (state) {
        case SearchFieldStateDisabled:
            self.reloadItem.enabled = NO;
            self.rightView = self.reloadItem;
            break;
            
        case SearchFieldStateReload:
            self.reloadItem.enabled = YES;
            self.rightView = self.reloadItem;
            break;
            
        case SearchFieldStateStop:
            self.rightView = self.stopItem;
            break;
    }
}

@end
